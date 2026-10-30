from time import perf_counter
from uuid import uuid4

import structlog
from app.infrastructure.llm.client import LlmProviderError
from app.modules.diagrams.errors import (
    InvalidDiagram,
    InvalidFrameExtraction,
    InvalidLocalCorrection,
)
from app.modules.diagrams.prompts import PROMPT_VERSION as DIAGRAM_PROMPT_VERSION
from app.modules.diagrams.schemas import Diagram, DiagramGenerationRequest
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import CreatedDiagramSession, DiagramSession
from app.modules.sessions.ports import SessionJobDispatcher
from app.modules.sessions.schemas import Answer, Question
from app.modules.sessions.service import SessionService
from app.workflows.clarification_context import build_clarification_context
from app.workflows.requirement_diagram_pipeline import RequirementDiagramPipeline

logger = structlog.get_logger(__name__)


class DiagramSessionWorkflow:
    def __init__(
        self,
        session_service: SessionService,
        job_dispatcher: SessionJobDispatcher,
        diagram_service: DiagramService,
        requirement_pipeline: RequirementDiagramPipeline | None = None,
        new_pipeline_enabled: bool = False,
    ) -> None:
        self._session_service = session_service
        self._job_dispatcher = job_dispatcher
        self._diagram_service = diagram_service
        self._requirement_pipeline = requirement_pipeline
        self._new_pipeline_enabled = new_pipeline_enabled

    async def create_session(
        self,
        description: str,
        language: str,
        client_address: str,
    ) -> CreatedDiagramSession:
        created_session = await self._session_service.create(description, language, client_address)
        session = created_session.session
        await self._session_service.transition(session.id, SessionStatus.ANALYZING)
        job_id = str(uuid4())
        session = await self._session_service.set_current_job(session.id, job_id)
        try:
            self._job_dispatcher.dispatch_session_processing(session.id, job_id)
        except Exception:
            await self._session_service.fail(session.id, "session_processing_failed")
            raise
        return CreatedDiagramSession(session=session, session_token=created_session.session_token)

    async def delete_session(self, session_id: str) -> None:
        session = await self._session_service.get(session_id)
        if session.current_job_id is not None:
            self._job_dispatcher.cancel(session.current_job_id)
        await self._session_service.delete(session_id)

    async def process_session(self, session_id: str) -> None:
        session = await self._session_service.get(session_id)
        if session.status not in {SessionStatus.ANALYZING, SessionStatus.GENERATING_DIAGRAM}:
            return
        if self._new_pipeline_enabled:
            await self._process_requirement_pipeline(session)
            return
        if session.status is SessionStatus.ANALYZING:
            session = await self._session_service.transition(
                session.id, SessionStatus.GENERATING_DIAGRAM
            )
        await self._generate_diagram(session)

    async def submit_answers(
        self, session_id: str, question_round: int, answers: list[Answer]
    ) -> DiagramSession:
        session = await self._session_service.submit_answers(session_id, question_round, answers)
        job_id = str(uuid4())
        session = await self._session_service.set_current_job(session.id, job_id)
        try:
            self._job_dispatcher.dispatch_session_processing(session.id, job_id)
        except Exception:
            await self._session_service.fail(session.id, "session_processing_failed")
            raise
        return session

    async def get_diagram(self, session_id: str) -> Diagram:
        session = await self._session_service.get(session_id)
        diagram_json = session.final_diagram_json or session.diagram_json
        if diagram_json is None:
            raise InvalidDiagram()
        return self._diagram_service.deserialize(diagram_json)

    async def _process_requirement_pipeline(self, session: DiagramSession) -> None:
        if self._requirement_pipeline is None:
            logger.error("requirement_pipeline_unavailable", session_id=session.id)
            await self._session_service.fail(session.id, "diagram_pipeline_unavailable")
            return
        logger.info("requirement_pipeline_processing_started", session_id=session.id)
        try:
            result = await self._requirement_pipeline.run(
                session.description,
                session.language,
                lambda phase: self._report_phase(session.id, phase),
            )
        except LlmProviderError as error:
            if error.retryable:
                logger.warning("requirement_pipeline_retry_scheduled", session_id=session.id)
                raise
            logger.warning("requirement_pipeline_failed", session_id=session.id)
            await self._session_service.fail(session.id, "diagram_generation_failed")
            return
        except (InvalidFrameExtraction, InvalidLocalCorrection, InvalidDiagram):
            logger.warning("requirement_pipeline_contract_failed", session_id=session.id)
            await self._session_service.fail(session.id, "diagram_generation_failed")
            return
        await self._session_service.transition(session.id, SessionStatus.GENERATING_DIAGRAM)
        await self._session_service.set_phase(session.id, "validating_diagram")
        await self._session_service.save_pipeline_result(
            session.id,
            result.assurance.raw.diagram.model_dump_json(by_alias=True),
            result.assurance.final.diagram.model_dump_json(by_alias=True),
            result.assurance.report.model_dump_json(by_alias=True),
            result.assurance.final.pipeline_versions.model_dump_json(by_alias=True),
        )
        logger.info("requirement_pipeline_result_saved", session_id=session.id)

    async def _report_phase(self, session_id: str, phase: str) -> None:
        await self._session_service.set_phase(session_id, phase)
        logger.info("requirement_pipeline_phase_changed", session_id=session_id, phase=phase)

    async def _generate_diagram(self, session: DiagramSession) -> None:
        generation_started_at = perf_counter()
        try:
            diagram = await self._diagram_service.generate(
                DiagramGenerationRequest(
                    description=session.description,
                    language=session.language,
                    clarification_context=build_clarification_context(
                        session.clarification_history
                    ),
                )
            )
        except LlmProviderError as error:
            if error.retryable:
                raise
            await self._session_service.fail(session.id, "diagram_generation_failed")
            return
        except InvalidDiagram:
            await self._session_service.fail(session.id, "diagram_generation_failed")
            return
        logger.info(
            "diagram_generation_completed",
            session_id=session.id,
            duration_ms=round((perf_counter() - generation_started_at) * 1_000),
        )
        await self._session_service.save_diagram(
            session.id,
            diagram.model_dump_json(by_alias=True),
            DIAGRAM_PROMPT_VERSION,
        )
