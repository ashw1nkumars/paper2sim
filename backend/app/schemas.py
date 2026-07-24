"""Pydantic models shared by the API and the Celery worker."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    ingesting = "ingesting"
    analyzing = "analyzing"
    generating = "generating"
    executing = "executing"
    repairing = "repairing"
    summarizing = "summarizing"
    completed = "completed"
    failed = "failed"


TERMINAL_STATUSES = {JobStatus.completed, JobStatus.failed}


class Analysis(BaseModel):
    """The paper's core claim and a plan for how to test it by simulation."""

    claim: str = ""
    why_it_matters: str = ""
    simulation_plan: str = ""


class ExecutionResult(BaseModel):
    """Outcome of running one generated script in the sandbox."""

    returncode: int = -1
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    artifacts: list[str] = Field(default_factory=list)  # paths relative to artifacts_dir
    result_json: dict[str, Any] | None = None
    attempt: int = 1
    timed_out: bool = False


class JobRecord(BaseModel):
    """The full lifecycle record for one submission, persisted in Redis."""

    id: str
    status: JobStatus = JobStatus.queued
    source_kind: str  # "pdf" | "arxiv" | "text"
    source_ref: str = ""  # filename, arxiv id, or txt filename
    title: str = ""
    created_at: str
    updated_at: str
    llm_provider: str = ""

    error: str | None = None
    paper_excerpt: str = ""
    analysis: Analysis | None = None
    code: str = ""
    execution: ExecutionResult | None = None
    verdict: str = ""
    summary: str = ""
