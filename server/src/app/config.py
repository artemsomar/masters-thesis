from functools import lru_cache
from typing import Annotated

from pydantic import AliasChoices, Field, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    rq_queue_name: str = "diagram-jobs"
    session_ttl_seconds: int = 86_400
    session_token_pepper: str = "development-only-change-me"
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "APP_GEMINI_API_KEY"),
    )
    gemini_model: str = ""
    gemini_embedding_model: str = ""
    gemini_embedding_dimensions: Annotated[int, Field(ge=1)] = 768
    max_clarification_rounds: Annotated[int, Field(ge=1)] = 3
    max_questions_per_round: Annotated[int, Field(ge=1)] = 7
    max_description_length: Annotated[int, Field(ge=1)] = 20_000
    max_answer_length: Annotated[int, Field(ge=1)] = 2_000
    session_creation_limit_per_day: Annotated[int, Field(ge=1)] = 100
    max_active_sessions_per_client: Annotated[int, Field(ge=1)] = 10
    llm_job_timeout_seconds: Annotated[int, Field(ge=1)] = 120
    llm_job_max_attempts: Annotated[int, Field(ge=1)] = 3
    llm_job_retry_intervals_seconds: tuple[Annotated[int, Field(ge=1)], ...] = (10, 20)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
