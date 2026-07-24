"""FastAPI application: submit papers, poll job status, serve generated artifacts."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import store
from .celery_app import celery_app
from .config import get_settings
from .schemas import JobRecord, JobStatus

settings = get_settings()

Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
Path(settings.artifacts_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(title="paper2sim API", version="0.1.0")

# The frontend is served same-origin via nginx in Docker; CORS is open so the
# Vite dev server (localhost:5173) can also talk to the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def rate_limit(request: Request) -> None:
    """Redis fixed-window limiter, keyed by client IP, on the expensive submit path."""
    ident = request.client.host if request.client else "anon"
    allowed, retry_after = store.check_rate_limit(
        f"submit:{ident}", settings.rate_limit_submit, settings.rate_limit_window_seconds
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({settings.rate_limit_submit} per hour). "
            f"Try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/papers", dependencies=[Depends(rate_limit)])
async def submit_paper(
    arxiv: str | None = Form(default=None),
    text: str | None = Form(default=None),
    title: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
) -> dict:
    job_id = uuid.uuid4().hex[:12]

    if file is not None and file.filename:
        contents = await file.read()
        if len(contents) > _MAX_UPLOAD_BYTES:
            raise HTTPException(413, "File too large (max 20 MB).")
        dest = Path(settings.uploads_dir) / f"{job_id}.pdf"
        dest.write_bytes(contents)
        source_kind, source_ref = "pdf", dest.name
        resolved_title = title or file.filename
    elif arxiv and arxiv.strip():
        source_kind, source_ref = "arxiv", arxiv.strip()
        resolved_title = title or f"arXiv:{arxiv.strip()}"
    elif text and text.strip():
        dest = Path(settings.uploads_dir) / f"{job_id}.txt"
        dest.write_text(text, encoding="utf-8")
        source_kind, source_ref = "text", dest.name
        resolved_title = title or "Pasted text"
    else:
        raise HTTPException(400, "Provide a PDF file, an arXiv id/URL, or pasted text.")

    now = store.now_iso()
    job = JobRecord(
        id=job_id,
        status=JobStatus.queued,
        source_kind=source_kind,
        source_ref=source_ref,
        title=resolved_title,
        created_at=now,
        updated_at=now,
    )
    store.save_job(job)
    celery_app.send_task("pipeline.run", args=[job_id])
    return {"job_id": job_id}


@app.get("/api/jobs")
def list_jobs() -> list[dict]:
    return [job.model_dump() for job in store.list_jobs()]


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = store.get_job(job_id)
    if job is None:
        raise HTTPException(404, "Job not found")
    return job.model_dump()


# Serve generated figures/animations. Relative artifact paths in a job record are
# rooted here, so the URL is /api/artifacts/<job_id>/run_<n>/figure_1.png.
app.mount(
    "/api/artifacts",
    StaticFiles(directory=settings.artifacts_dir, check_dir=False),
    name="artifacts",
)
