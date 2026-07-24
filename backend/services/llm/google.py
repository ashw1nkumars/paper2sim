"""Google AI Studio (Gemini) provider via its OpenAI-compatible endpoint."""

from __future__ import annotations

from core.config import get_settings

from .openai_compat import chat_complete

_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


class GoogleProvider:
    name = "google"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.google_ai_studio_api_key:
            raise RuntimeError("GOOGLE_AI_STUDIO_API_KEY is not set.")
        self._key = settings.google_ai_studio_api_key
        self._model = settings.google_model
        self._max_tokens = settings.llm_max_tokens

    def complete(self, system: str, user: str) -> str:
        return chat_complete(_URL, self._key, self._model, system, user, self._max_tokens)
