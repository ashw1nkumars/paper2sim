"""Redis-backed persistence: job records, a job index, a text cache, and the
rate-limiter counters. Redis is the single source of truth for job state so the
API and the Celery worker (separate processes) stay in sync."""

from __future__ import annotations

from datetime import UTC, datetime

import redis

from core.config import get_settings
from models.job import JobRecord, JobStatus

_settings = get_settings()
_r = redis.Redis.from_url(_settings.redis_url, decode_responses=True)

_JOB_KEY = "paper2sim:job:{}"
_JOB_INDEX = "paper2sim:jobs"  # sorted set: member=job_id, score=created ts
_CACHE_KEY = "paper2sim:cache:{}"
_RL_KEY = "paper2sim:rl:{}"


def client() -> redis.Redis:
    return _r


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


# --- Job records -----------------------------------------------------------
def save_job(job: JobRecord) -> None:
    job.updated_at = now_iso()
    _r.set(_JOB_KEY.format(job.id), job.model_dump_json())
    score = datetime.fromisoformat(job.created_at).timestamp()
    _r.zadd(_JOB_INDEX, {job.id: score})


def get_job(job_id: str) -> JobRecord | None:
    raw = _r.get(_JOB_KEY.format(job_id))
    return JobRecord.model_validate_json(raw) if raw else None


def list_jobs(limit: int = 50) -> list[JobRecord]:
    ids = _r.zrevrange(_JOB_INDEX, 0, limit - 1)
    jobs = [get_job(jid) for jid in ids]
    return [j for j in jobs if j is not None]


def set_status(job: JobRecord, status: JobStatus) -> JobRecord:
    job.status = status
    save_job(job)
    return job


# --- Generic cache (used for arXiv fetches) --------------------------------
def cache_get(key: str) -> str | None:
    return _r.get(_CACHE_KEY.format(key))


def cache_set(key: str, value: str, ttl: int = 86400) -> None:
    _r.set(_CACHE_KEY.format(key), value, ex=ttl)


# --- Rate limiting (fixed-window counter) ----------------------------------
def check_rate_limit(key: str, limit: int, window: int) -> tuple[bool, int]:
    """Increment the window counter for ``key``. Returns ``(allowed, retry_after)``.

    The first hit in a window sets the TTL, so the counter self-expires.
    """
    rk = _RL_KEY.format(key)
    count = _r.incr(rk)
    if count == 1:
        _r.expire(rk, window)
    ttl = _r.ttl(rk)
    retry_after = ttl if ttl and ttl > 0 else window
    return count <= limit, retry_after
