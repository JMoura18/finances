from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="dev")
    database_url: str = Field(
        default="postgresql+asyncpg://cofre:cofre@localhost:5432/cofre"
    )
    anthropic_api_key: str | None = None
    anthropic_model_main: str = "claude-opus-4-7"
    anthropic_model_cheap: str = "claude-haiku-4-5-20251001"
    firebase_credentials_path: str | None = None
    snaptrade_client_id: str | None = None
    snaptrade_consumer_key: str | None = None
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
