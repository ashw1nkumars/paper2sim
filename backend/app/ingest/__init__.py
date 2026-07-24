"""Turn a submission into plain text the LLM can reason about."""

from __future__ import annotations

from pathlib import Path

from ..config import get_settings
from ..schemas import JobRecord
from . import arxiv, pdf

_settings = get_settings()

# Cap how much paper text we feed downstream (keeps prompts + storage bounded).
MAX_CHARS = 24_000


def get_text(job: JobRecord) -> str:
    if job.source_kind == "pdf":
        path = Path(_settings.uploads_dir) / job.source_ref
        text = pdf.extract_text(str(path))
    elif job.source_kind == "arxiv":
        text = arxiv.fetch_text(job.source_ref)
    elif job.source_kind == "text":
        path = Path(_settings.uploads_dir) / job.source_ref
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(f"Unknown source_kind: {job.source_kind}")

    text = text.strip()
    if not text:
        raise ValueError("Could not extract any text from the submission.")
    return text[:MAX_CHARS]
