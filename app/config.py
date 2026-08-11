"""Typed settings (Pydantic v2)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis_url: str = "redis://localhost:6379/0"
    use_fake_redis: bool = False
    # Run jobs inline instead of on a worker (tests / no-worker demos).
    queue_sync: bool = False

    llm_backend: str = "echo"  # echo | gemini
    google_api_key: str = ""
    model_name: str = "gemini-2.0-flash"

    max_retries: int = 3

    otel_exporter: str = "console"  # console | otlp | none
    otel_endpoint: str = "http://localhost:4318/v1/traces"

    @property
    def gemini_ready(self) -> bool:
        return self.llm_backend == "gemini" and bool(self.google_api_key)


settings = Settings()
