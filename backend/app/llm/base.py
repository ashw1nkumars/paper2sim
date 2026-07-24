"""LLM provider abstraction + factory.

The pipeline only depends on the tiny ``complete(system, user) -> str`` surface,
so providers are trivially swappable. ``get_provider()`` picks Anthropic when a
key is configured and otherwise falls back to the deterministic mock, which lets
the whole app run end-to-end with no API key.
"""

from __future__ import annotations

from typing import Protocol

from ..config import get_settings


class LLMProvider(Protocol):
    name: str

    def complete(self, system: str, user: str) -> str: ...


def get_provider() -> LLMProvider:
    settings = get_settings()
    choice = settings.llm_provider.lower()

    if choice == "mock":
        from .mock import MockProvider

        return MockProvider()

    if choice == "anthropic" or (choice == "auto" and settings.anthropic_api_key):
        from .anthropic import AnthropicProvider

        return AnthropicProvider()

    from .mock import MockProvider

    return MockProvider()
