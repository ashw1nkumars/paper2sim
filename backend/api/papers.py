"""Paper submission endpoint: accepts a PDF, an arXiv id/URL, or pasted text."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

import store
from api.deps import rate_limit
from core.config import get_settings
from models.job import JobRecord, JobStatus
from worker import celery_app

settings = get_settings()

router = APIRouter()

_MAX_UPLOAD_BYTES = 20 * 1024 * 1024


@router.post("/api/papers", dependencies=[Depends(rate_limit)])
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
