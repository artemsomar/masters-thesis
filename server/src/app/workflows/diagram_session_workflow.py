from time import perf_counter
from uuid import uuid4

import structlog
from app.infrastructure.llm.client import LlmProviderError
from app.modules.clarifications.errors import InvalidClarificationResult
from app.modules.clarifications.prompts import PROMPT_VERSION as CLARIFICATION_PROMPT_VERSION
from app.modules.clarifications.service import ClarificationService
from app.modules.diagrams.errors import InvalidDiagram
from app.modules.diagrams.prompts import PROMPT_VERSION as DIAGRAM_PROMPT_VERSION
from app.modules.diagrams.schemas import Diagram, DiagramGenerationRequest
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession
from app.modules.sessions.ports import SessionJobDispatcher
from app.modules.sessions.schemas import Answer, Question
from app.modules.sessions.service import SessionService
from app.workflows.clarification_context import build_clarification_context

logger = structlog.get_logger(__name__)


class DiagramSessionWorkflow:
    def __init__(
        self,
        session_service: SessionService,
        job_dispatcher: SessionJobDispatcher,
        clarification_service: ClarificationService,
        diagram_service: DiagramService,
        max_clarification_rounds: int,
    ) -> None:
        self._session_service = session_service
        self._job_dispatcher = job_dispatcher
        self._clarification_service = clarification_service
        self._diagram_service = diagram_service
        self._max_clarification_rounds = max_clarification_rounds

    async def create_session(
        self,
        description: str,
        language: str,
        client_address: str,
        clarifications_enabled: bool,
    ) -> tuple[DiagramSession, str]:
        session, token = await self._session_service.create(
            description, language, client_address, clarifications_enabled
        )
        target = (
            SessionStatus.ANALYZING
            if session.clarifications_enabled
            else SessionStatus.GENERATING_DIAGRAM
        )
        await self._session_service.transition(session.id, target)
        job_id = str(uuid4())
        session = await self._session_service.set_current_job(session.id, job_id)
        try:
            self._job_dispatcher.dispatch_session_processing(session.id, job_id)
        except Exception:
            await self._session_service.fail(session.id, "session_processing_failed")
            raise
        return session, token

    async def delete_session(self, session_id: str) -> None:
        session = await self._session_service.get(session_id)
        if session.current_job_id is not None:
            self._job_dispatcher.cancel(session.current_job_id)
        await self._session_service.delete(session_id)

    async def process_session(self, session_id: str) -> None:
        session = await self._session_service.get(session_id)
        if session.status not in {SessionStatus.ANALYZING, SessionStatus.GENERATING_DIAGRAM}:
            return
        if self._can_request_clarifications(session):
            session = await self._request_clarifications(session)
            if session.status is not SessionStatus.GENERATING_DIAGRAM:
                return
        elif session.status is SessionStatus.ANALYZING:
            session = await self._session_service.transition(
                session.id, SessionStatus.GENERATING_DIAGRAM
            )
        await self._generate_diagram(session)

    async def _request_clarifications(self, session: DiagramSession) -> DiagramSession:
        clarification_started_at = perf_counter()
        try:
            result = await self._clarification_service.ask(
                session.description,
                session.language,
                build_clarification_context(session.clarification_history),
            )
        except LlmProviderError as error:
            if error.retryable:
                raise
            return await self._session_service.fail(session.id, "clarification_failed")
        except InvalidClarificationResult:
            return await self._session_service.fail(session.id, "clarification_failed")
        logger.info(
            "clarification_completed",
            session_id=session.id,
            duration_ms=round((perf_counter() - clarification_started_at) * 1_000),
        )
        questions = [
            Question(id=question.id, text=question.text, required=question.required)
            for question in result.questions
        ]
        return await self._session_service.save_clarification_result(
            session.id,
            questions,
            CLARIFICATION_PROMPT_VERSION,
        )

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
        if session.diagram_json is None:
            raise InvalidDiagram()
        return self._diagram_service.deserialize(session.diagram_json)

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

    def _can_request_clarifications(self, session: DiagramSession) -> bool:
        return (
            session.clarifications_enabled
            and session.question_round < self._max_clarification_rounds
        )
