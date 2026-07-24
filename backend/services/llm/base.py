"""LLM provider abstraction + factory.

The pipeline only depends on the tiny ``complete(system, user) -> str`` surface,
so providers are trivially swappable. ``get_provider()`` picks Anthropic when a
key is configured and otherwise falls back to the deterministic mock, which lets
the whole app run end-to-end with no API key.
"""

from __future__ import annotations

from typing import Protocol

from core.config import get_settings


class LLMProvider(Protocol):
    name: str

    def complete(self, system: str, user: str) -> str: ...


def get_provider() -> LLMProvider:
    settings = get_settings()
    choice = settings.llm_provider.lower()

    if choice == "anthropic":
        from .anthropic import AnthropicProvider

        return AnthropicProvider()
    if choice == "groq":
        from .groq import GroqProvider

        return GroqProvider()
    if choice == "cerebras":
        from .cerebras import CerebrasProvider

        return CerebrasProvider()
    if choice == "google":
        from .google import GoogleProvider

        return GoogleProvider()
    if choice == "openrouter":
        from .openrouter import OpenRouterProvider

        return OpenRouterProvider()
    if choice == "auto":
        if settings.anthropic_api_key:
            from .anthropic import AnthropicProvider

            return AnthropicProvider()
        if settings.groq_api_key:
            from .groq import GroqProvider

            return GroqProvider()
        if settings.cerebras_api_key:
            from .cerebras import CerebrasProvider

            return CerebrasProvider()
        if settings.google_ai_studio_api_key:
            from .google import GoogleProvider

            return GoogleProvider()
        if settings.openrouter_api_key:
            from .openrouter import OpenRouterProvider

            return OpenRouterProvider()

    from .mock import MockProvider

    return MockProvider()
