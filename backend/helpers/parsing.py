"""Pure text-parsing helpers for the pipeline: pull code out of an LLM response,
parse the analysis JSON, and derive a verdict from an execution result."""

from __future__ import annotations

import json
import re

from models.job import Analysis, ExecutionResult

_CODE_FENCE = re.compile(r"```(?:python)?\s*\n?(.*?)```", re.DOTALL)
_CODE_FENCE_OPEN = re.compile(r"```(?:python)?\s*\n(.*)", re.DOTALL)
_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


def extract_code(text: str) -> str:
    match = _CODE_FENCE.search(text)
    if match:
        return match.group(1).strip()
    # Tolerate a truncated response whose closing fence is missing.
    match = _CODE_FENCE_OPEN.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


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
