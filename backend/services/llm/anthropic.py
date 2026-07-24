"""Anthropic Claude provider."""

from __future__ import annotations

from core.config import get_settings


class AnthropicProvider:
    name = "anthropic"

    def __init__(self) -> None:
        from anthropic import Anthropic  # imported lazily so the mock path needs no SDK

        settings = get_settings()
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        self._max_tokens = settings.llm_max_tokens

    def complete(self, system: str, user: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in message.content if block.type == "text")
