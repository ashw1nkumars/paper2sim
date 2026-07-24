"""OpenRouter provider (aggregator with an OpenAI-compatible API)."""

from __future__ import annotations

from ..config import get_settings
from .openai_compat import chat_complete

_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider:
    name = "openrouter"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")
        self._key = settings.openrouter_api_key
        self._model = settings.openrouter_model
        self._max_tokens = settings.llm_max_tokens

    def complete(self, system: str, user: str) -> str:
        return chat_complete(_URL, self._key, self._model, system, user, self._max_tokens)
