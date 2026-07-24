"""Shared client for OpenAI-compatible chat-completions APIs (Groq, Cerebras, ...).

Keeps provider files tiny: they just supply a base URL, key, and model. Includes a
small backoff on 429 and surfaces the response body in errors (the useful
rate-limit / validation detail lives there, not in the status line).
"""

from __future__ import annotations

import time

import httpx

_MAX_RETRIES = 3


def chat_complete(
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    timeout: float = 120.0,
) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    resp: httpx.Response | None = None
    for attempt in range(_MAX_RETRIES):
        resp = httpx.post(base_url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 429 and attempt < _MAX_RETRIES - 1:
            retry_after = resp.headers.get("retry-after", "")
            if retry_after.replace(".", "", 1).isdigit():
                delay = float(retry_after)
            else:
                delay = 5.0 * (attempt + 1)
            time.sleep(min(delay, 20.0))
            continue
        break

    assert resp is not None
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"{model} API error {resp.status_code}: {resp.text[:600]}") from exc
    return resp.json()["choices"][0]["message"]["content"]
