"""Shared FastAPI dependencies."""

from __future__ import annotations

from fastapi import HTTPException, Request

import store
from core.config import get_settings

settings = get_settings()


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
