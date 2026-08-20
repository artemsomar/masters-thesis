from dataclasses import dataclass

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.config import Settings, get_settings
from app.infrastructure.events.redis_session_events import RedisSessionEventBroker
from app.infrastructure.llm.gemini_structured_client import GeminiStructuredOutputClient
from app.infrastructure.queue.rq_session_dispatcher import RqSessionJobDispatcher
from app.infrastructure.rate_limits.redis_session_creation_limiter import (
    RedisSessionCreationLimiter,
)
from app.infrastructure.repositories.redis_session_repository import RedisSessionRepository
from app.logging_config import configure_logging
from app.modules.clarifications.service import ClarificationService
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings
    async_redis: AsyncRedis
    sync_redis: Redis
    session_service: SessionService
    session_event_broker: RedisSessionEventBroker
    clarification_service: ClarificationService
    diagram_service: DiagramService
    diagram_session_workflow: DiagramSessionWorkflow


def build_container(settings: Settings | None = None) -> ApplicationContainer:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    redis_url = str(resolved_settings.redis_url)
    async_redis = AsyncRedis.from_url(redis_url, decode_responses=True)
    sync_redis = Redis.from_url(redis_url)
    event_broker = RedisSessionEventBroker(async_redis)
    session_service = SessionService(
        repository=RedisSessionRepository(async_redis, resolved_settings.session_ttl_seconds),
        event_publisher=event_broker,
        creation_limiter=RedisSessionCreationLimiter(
            async_redis,
            resolved_settings.session_ttl_seconds,
            resolved_settings.session_creation_limit_per_day,
            resolved_settings.max_active_sessions_per_client,
        ),
        token_pepper=resolved_settings.session_token_pepper,
        ttl_seconds=resolved_settings.session_ttl_seconds,
        max_description_length=resolved_settings.max_description_length,
        max_answer_length=resolved_settings.max_answer_length,
    )
    dispatcher = RqSessionJobDispatcher(
        sync_redis,
        resolved_settings.rq_queue_name,
        resolved_settings.llm_job_timeout_seconds,
        resolved_settings.llm_job_max_attempts,
        list(resolved_settings.llm_job_retry_intervals_seconds),
    )
    llm_client = GeminiStructuredOutputClient(
        resolved_settings.gemini_api_key, resolved_settings.gemini_model
    )
    clarification_service = ClarificationService(
        llm_client, max_questions_per_round=resolved_settings.max_questions_per_round
    )
    diagram_service = DiagramService(llm_client)
    return ApplicationContainer(
        settings=resolved_settings,
        async_redis=async_redis,
        sync_redis=sync_redis,
        session_service=session_service,
        session_event_broker=event_broker,
        clarification_service=clarification_service,
        diagram_service=diagram_service,
        diagram_session_workflow=DiagramSessionWorkflow(
            session_service,
            dispatcher,
            clarification_service,
            diagram_service,
            resolved_settings.max_clarification_rounds,
        ),
    )
