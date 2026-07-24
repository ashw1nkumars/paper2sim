"""Application settings, loaded from environment variables (12-factor style)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Redis / Celery -----------------------------------------------------
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    # --- LLM ----------------------------------------------------------------
    # "auto" -> anthropic if a key is present, else the deterministic mock.
    llm_provider: str = "auto"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    llm_max_tokens: int = 8000
    max_repair_attempts: int = 3

    # --- Sandbox ------------------------------------------------------------
    sandbox_timeout_seconds: int = 60
    sandbox_max_memory_mb: int = 2048
    sandbox_max_output_mb: int = 50
    sandbox_max_procs: int = 256

    # --- Storage ------------------------------------------------------------
    uploads_dir: str = "/data/uploads"
    artifacts_dir: str = "/data/artifacts"

    # --- Rate limiting ------------------------------------------------------
    rate_limit_submit: int = 20
    rate_limit_window_seconds: int = 3600

    @property
    def broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
