from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Resume Analyzer"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: list[str] = ["*"]

    redis_url: str | None = None
    cache_ttl_seconds: int = 3600

    llm_api_key: str | None = None
    llm_api_url: str = "https://api.deepseek.com/v1/chat/completions"
    llm_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 30.0

    max_upload_size_mb: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
