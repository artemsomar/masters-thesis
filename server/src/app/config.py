from functools import lru_cache

from pydantic import RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    rq_queue_name: str = "diagram-jobs"
    session_ttl_seconds: int = 86_400
    session_token_pepper: str = "development-only-change-me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
