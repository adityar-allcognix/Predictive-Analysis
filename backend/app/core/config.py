from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"

    # Default is for local docker-compose. Override with env var DATABASE_URL in prod.
    database_url: str = "postgresql://postgres:postgres@localhost:5433/predictive_analysis"

    cors_origins: str = "http://localhost:3000"

    use_crewai: bool = True


settings = Settings()
