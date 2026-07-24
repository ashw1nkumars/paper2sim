"""HTTP layer: the aggregated API router."""

from fastapi import APIRouter

from api.health import router as health_router
from api.jobs import router as jobs_router
from api.papers import router as papers_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(papers_router)
api_router.include_router(jobs_router)
