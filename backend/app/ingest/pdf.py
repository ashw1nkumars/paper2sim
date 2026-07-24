"""Extract text from an uploaded PDF."""

from __future__ import annotations

from pypdf import PdfReader


def extract_text(path: str) -> str:
    reader = PdfReader(path)
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts).strip()
