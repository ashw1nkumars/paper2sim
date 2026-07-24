"""Celery application. Redis is both the broker and the result backend."""

from celery import Celery

from core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "paper2sim",
    broker=_settings.broker,
    backend=_settings.backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=86400,
    task_time_limit=900,  # hard ceiling per job (s); the sandbox has its own limit
    worker_prefetch_multiplier=1,
    # Tasks live here; imported lazily when the worker boots (avoids import cycles).
    imports=("services.pipeline",),
)
