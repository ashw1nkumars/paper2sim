"""Cerebras provider (fast open models via an OpenAI-compatible API)."""

from __future__ import annotations

from core.config import get_settings

from .openai_compat import chat_complete

_URL = "https://api.cerebras.ai/v1/chat/completions"


class CerebrasProvider:
    name = "cerebras"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.cerebras_api_key:
            raise RuntimeError("CEREBRAS_API_KEY is not set.")
        self._key = settings.cerebras_api_key
        self._model = settings.cerebras_model
        self._max_tokens = settings.llm_max_tokens

    def complete(self, system: str, user: str) -> str:
        return chat_complete(_URL, self._key, self._model, system, user, self._max_tokens)
