"""Job status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

import store

router = APIRouter()


@router.get("/api/jobs")
def list_jobs() -> list[dict]:
    return [job.model_dump() for job in store.list_jobs()]


@router.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job.model_dump()
