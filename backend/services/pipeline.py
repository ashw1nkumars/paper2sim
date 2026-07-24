"""The Celery task that drives a submission through every stage:

    ingest -> analyze -> generate -> execute (with a repair loop) -> summarize

Each stage writes progress back to the Redis job record so the UI can follow
along in real time.
"""

from __future__ import annotations

import store
from core.config import get_settings
from helpers.parsing import derive_verdict, extract_code, parse_analysis
from models.job import ExecutionResult, JobStatus
from services.ingest import get_text
from services.llm import get_provider, prompts
from services.sandbox import run_code
from worker import celery_app

_settings = get_settings()


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
        # A run only counts as successful if it exits cleanly AND produced at
        # least one figure; a clean run with no figures is repaired too.
        execution: ExecutionResult | None = None
        for attempt in range(1, _settings.max_repair_attempts + 1):
            store.set_status(job, JobStatus.executing if attempt == 1 else JobStatus.repairing)
            execution = run_code(job_id, code, attempt)
            job.code = code
            job.execution = execution
            store.save_job(job)
            if execution.returncode == 0 and execution.artifacts:
                break
            if attempt < _settings.max_repair_attempts:
                if execution.returncode != 0:
                    feedback = execution.stderr.strip()
                    if not feedback:
                        # A resource-limit kill (e.g. SIGXCPU, rc -24) leaves no
                        # traceback, so tell the model to make the code faster/lighter.
                        feedback = (
                            f"The script was killed (exit code {execution.returncode}) with no "
                            "output, almost certainly for exceeding the CPU-time or memory limit. "
                            "Make it dramatically faster and lighter: shrink sample sizes, replace "
                            "Python loops with vectorized numpy, avoid O(n^2) work, and keep total "
                            "runtime well under 40 seconds. Still save figure_1.png and print the "
                            "final RESULT_JSON line."
                        )
                else:
                    feedback = (
                        "The script exited successfully but saved no figures. You MUST "
                        "save at least one figure to the current directory as figure_1.png "
                        "(use matplotlib with the Agg backend), and still print the final "
                        "RESULT_JSON line."
                    )
                code = extract_code(
                    provider.complete(prompts.REPAIR_SYSTEM, prompts.repair_user(code, feedback))
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

    except Exception as exc:  # noqa: BLE001 - record any failure on the job
        job.error = f"{type(exc).__name__}: {exc}"
        job.verdict = "error"
        store.set_status(job, JobStatus.failed)
        raise
