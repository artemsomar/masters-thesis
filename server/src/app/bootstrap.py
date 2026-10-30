from dataclasses import dataclass
from pathlib import Path

from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.config import Settings, get_settings
from app.infrastructure.embeddings.gemini_embedding_client import GeminiEmbeddingClient
from app.infrastructure.events.redis_session_events import RedisSessionEventBroker
from app.infrastructure.llm.gemini_structured_client import GeminiStructuredOutputClient
from app.infrastructure.queue.rq_session_dispatcher import RqSessionJobDispatcher
from app.infrastructure.rate_limits.redis_session_creation_limiter import (
    RedisSessionCreationLimiter,
)
from app.infrastructure.repositories.redis_evaluation_run_repository import (
    RedisEvaluationRunRepository,
)
from app.infrastructure.repositories.redis_session_repository import RedisSessionRepository
from app.infrastructure.repositories.redis_project_repository import RedisProjectRepository
from app.modules.projects.service import ProjectService
from app.logging_config import configure_logging
from app.modules.diagrams.defect_detection import RequirementDefectDetector
from app.modules.diagrams.diagram_assembly import DiagramAssembler
from app.modules.diagrams.diagram_assurance import DiagramAssuranceService
from app.modules.diagrams.frame_extraction import FrameExtractionService
from app.modules.diagrams.local_correction import LocalCorrectionService
from app.modules.diagrams.requirement_graph import RequirementGraphBuilder, RequirementGraphSettings
from app.modules.diagrams.service import DiagramService
from app.modules.evaluation.dataset_reader import EvaluationDatasetReader
from app.modules.evaluation.run_service import EvaluationRunService
from app.modules.evaluation.service import EvaluationService
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow
from app.workflows.evaluation_run_workflow import EvaluationRunWorkflow
from app.workflows.requirement_diagram_pipeline import RequirementDiagramPipeline
from app.workflows.evaluation_workflow import EvaluationWorkflow


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings
    async_redis: AsyncRedis
    sync_redis: Redis
    session_service: SessionService
    session_event_broker: RedisSessionEventBroker
    diagram_service: DiagramService
    diagram_session_workflow: DiagramSessionWorkflow
    project_service: ProjectService
    evaluation_service: EvaluationService
    evaluation_workflow: EvaluationWorkflow
    evaluation_run_service: EvaluationRunService
    evaluation_run_workflow: EvaluationRunWorkflow


def build_container(settings: Settings | None = None) -> ApplicationContainer:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level, resolved_settings.log_file_path)
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
        resolved_settings.evaluation_job_timeout_seconds,
    )
    llm_client = GeminiStructuredOutputClient(
        resolved_settings.gemini_api_key, resolved_settings.gemini_model
    )
    embedding_client = (
        GeminiEmbeddingClient(
            resolved_settings.gemini_api_key,
            resolved_settings.gemini_embedding_model,
            resolved_settings.gemini_embedding_dimensions,
        )
        if resolved_settings.gemini_embedding_model
        else None
    )
    diagram_service = DiagramService(llm_client)
    requirement_pipeline = _build_requirement_pipeline(resolved_settings, llm_client, embedding_client)
    project_service = ProjectService(
        RedisProjectRepository(async_redis),
        resolved_settings.session_token_pepper,
        resolved_settings.session_ttl_seconds,
    )
    evaluation_service = EvaluationService(
        EvaluationDatasetReader(),
        embedding_client,
        resolved_settings.max_description_length,
        resolved_settings.evaluation_actor_similarity_threshold,
        resolved_settings.evaluation_use_case_similarity_threshold,
    )
    evaluation_workflow = EvaluationWorkflow(requirement_pipeline, evaluation_service)
    evaluation_run_service = EvaluationRunService(
        RedisEvaluationRunRepository(async_redis, resolved_settings.evaluation_run_ttl_seconds)
    )
    evaluation_run_workflow = EvaluationRunWorkflow(
        evaluation_run_service,
        dispatcher,
        evaluation_service,
        evaluation_workflow,
        Path(resolved_settings.evaluation_dataset_path),
    )
    return ApplicationContainer(
        settings=resolved_settings,
        async_redis=async_redis,
        sync_redis=sync_redis,
        session_service=session_service,
        session_event_broker=event_broker,
        diagram_service=diagram_service,
        diagram_session_workflow=DiagramSessionWorkflow(
            session_service,
            dispatcher,
            diagram_service,
            requirement_pipeline,
            resolved_settings.new_diagram_pipeline_enabled,
        ),
        project_service=project_service,
        evaluation_service=evaluation_service,
        evaluation_workflow=evaluation_workflow,
        evaluation_run_service=evaluation_run_service,
        evaluation_run_workflow=evaluation_run_workflow,
    )


def _build_requirement_pipeline(
    settings: Settings,
    llm_client: GeminiStructuredOutputClient,
    embedding_client: GeminiEmbeddingClient | None = None,
) -> RequirementDiagramPipeline:
    return RequirementDiagramPipeline(
        FrameExtractionService(llm_client, settings.max_description_length),
        RequirementGraphBuilder(
            embedding_client
            if embedding_client is not None
            else (
                GeminiEmbeddingClient(
                    settings.gemini_api_key,
                    settings.gemini_embedding_model,
                    settings.gemini_embedding_dimensions,
                )
                if settings.gemini_embedding_model
                else None
            ),
            RequirementGraphSettings(settings.requirement_graph_similarity_threshold),
        ),
        RequirementDefectDetector(),
        LocalCorrectionService(llm_client),
        DiagramAssembler(),
        DiagramAssuranceService(),
        settings.gemini_embedding_model or None,
        settings.requirement_graph_similarity_threshold,
    )
