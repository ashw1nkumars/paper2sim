"""The Celery task that drives a submission through every stage:

    ingest -> analyze -> generate -> execute (with a repair loop) -> summarize

Each stage writes progress back to the Redis job record so the UI can follow
along in real time.
"""

from __future__ import annotations

import json
import re

from .. import store
from ..celery_app import celery_app
from ..config import get_settings
from ..ingest import get_text
from ..llm import get_provider, prompts
from ..sandbox import run_code
from ..schemas import Analysis, ExecutionResult, JobStatus

_settings = get_settings()

_CODE_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def extract_code(text: str) -> str:
    match = _CODE_FENCE.search(text)
    return (match.group(1) if match else text).strip()


def parse_analysis(text: str) -> Analysis:
    match = _JSON_OBJECT.search(text)
    if match:
        try:
            data = json.loads(match.group(0))
            return Analysis(
                claim=str(data.get("claim", "")).strip(),
                why_it_matters=str(data.get("why_it_matters", "")).strip(),
                simulation_plan=str(data.get("simulation_plan", "")).strip(),
            )
        except (json.JSONDecodeError, TypeError):
            pass
    # Fall back to using the raw text as the claim so the pipeline still proceeds.
    return Analysis(claim=text.strip()[:500])


def derive_verdict(execution: ExecutionResult | None) -> str:
    if execution is None:
        return "error"
    if execution.returncode != 0:
        return "error"
    if execution.result_json and execution.result_json.get("verdict"):
        return str(execution.result_json["verdict"])
    return "inconclusive"


@celery_app.task(name="pipeline.run", bind=True)
def run_pipeline(self, job_id: str) -> str:  # noqa: ARG001 (self required by bind=True)
    job = store.get_job(job_id)
    if job is None:
        return "missing"

    provider = get_provider()
    job.llm_provider = provider.name

    try:
        # 1. Ingest ----------------------------------------------------------
        store.set_status(job, JobStatus.ingesting)
        paper_text = get_text(job)
        job.paper_excerpt = paper_text[:4000]
        store.save_job(job)

        # 2. Analyze ---------------------------------------------------------
        store.set_status(job, JobStatus.analyzing)
        analysis = parse_analysis(
            provider.complete(prompts.ANALYZE_SYSTEM, prompts.analyze_user(paper_text))
        )
        job.analysis = analysis
        store.save_job(job)

        # 3. Generate --------------------------------------------------------
        store.set_status(job, JobStatus.generating)
        code = extract_code(
            provider.complete(prompts.GENERATE_SYSTEM, prompts.generate_user(analysis, paper_text))
        )
        job.code = code
        store.save_job(job)

        # 4. Execute, with a repair loop ------------------------------------
        execution: ExecutionResult | None = None
        for attempt in range(1, _settings.max_repair_attempts + 1):
            store.set_status(job, JobStatus.executing if attempt == 1 else JobStatus.repairing)
            execution = run_code(job_id, code, attempt)
            job.code = code
            job.execution = execution
            store.save_job(job)
            if execution.returncode == 0:
                break
            if attempt < _settings.max_repair_attempts:
                code = extract_code(
                    provider.complete(
                        prompts.REPAIR_SYSTEM, prompts.repair_user(code, execution.stderr)
                    )
                )

        # 5. Summarize -------------------------------------------------------
        store.set_status(job, JobStatus.summarizing)
        if execution is not None and execution.returncode == 0:
            job.summary = provider.complete(
                prompts.SUMMARIZE_SYSTEM, prompts.summarize_user(analysis, execution)
            ).strip()
        else:
            job.summary = (
                "The generated simulation could not be executed successfully after "
                f"{_settings.max_repair_attempts} attempt(s). See the error output."
            )
        job.verdict = derive_verdict(execution)

        succeeded = execution is not None and execution.returncode == 0
        final = JobStatus.completed if succeeded else JobStatus.failed
        store.set_status(job, final)
        return final.value

    except Exception as exc:  # noqa: BLE001 — record any failure on the job
        job.error = f"{type(exc).__name__}: {exc}"
        job.verdict = "error"
        store.set_status(job, JobStatus.failed)
        raise
