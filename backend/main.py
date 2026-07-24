"""FastAPI application: submit papers, poll job status, serve generated artifacts."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import api_router
from core.config import get_settings

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

app.include_router(api_router)

# Serve generated figures/animations. Relative artifact paths in a job record are
# rooted here, so the URL is /api/artifacts/<job_id>/run_<n>/figure_1.png.
app.mount(
    "/api/artifacts",
    StaticFiles(directory=settings.artifacts_dir, check_dir=False),
    name="artifacts",
)
