from time import perf_counter
from uuid import uuid4

import structlog
from app.modules.analysis.errors import AnalysisProviderError, InvalidAnalysisResult
from app.modules.analysis.prompts import PROMPT_VERSION as ANALYSIS_PROMPT_VERSION
from app.modules.analysis.schemas import AnalysisAnswer, AnalysisQuestion
from app.modules.analysis.service import RequirementsAnalysisService
from app.modules.diagrams.errors import DiagramProviderError, InvalidDiagram
from app.modules.diagrams.prompts import PROMPT_VERSION as DIAGRAM_PROMPT_VERSION
from app.modules.diagrams.schemas import Diagram, DiagramGenerationAnswer, DiagramGenerationRequest
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession
from app.modules.sessions.ports import SessionJobDispatcher
from app.modules.sessions.schemas import Answer, Question
from app.modules.sessions.service import SessionService

logger = structlog.get_logger(__name__)


class DiagramSessionWorkflow:
    def __init__(
        self,
        session_service: SessionService,
        job_dispatcher: SessionJobDispatcher,
        analysis_service: RequirementsAnalysisService,
        diagram_service: DiagramService,
        max_analysis_rounds: int,
    ) -> None:
        self._session_service = session_service
        self._job_dispatcher = job_dispatcher
        self._analysis_service = analysis_service
        self._diagram_service = diagram_service
        self._max_analysis_rounds = max_analysis_rounds

    async def create_session(
        self, description: str, language: str, client_address: str
    ) -> tuple[DiagramSession, str]:
        session, token = await self._session_service.create(description, language, client_address)
        await self._session_service.transition(session.id, SessionStatus.ANALYZING)
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
        analysis_started_at = perf_counter()
        try:
            result = await self._analysis_service.analyze(
                session.description,
                session.language,
                [
                    AnalysisAnswer(question_id=answer.question_id, value=answer.value)
                    for answer in session.answers
                ],
                session.question_round < self._max_analysis_rounds,
            )
        except AnalysisProviderError as error:
            if error.retryable:
                raise
            await self._session_service.fail(session.id, "analysis_failed")
            return
        except InvalidAnalysisResult:
            await self._session_service.fail(session.id, "analysis_failed")
            return
        logger.info(
            "requirements_analysis_completed",
            session_id=session.id,
            duration_ms=round((perf_counter() - analysis_started_at) * 1_000),
        )
        questions = [
            Question(id=question.id, text=question.text, required=question.required)
            for question in result.questions
        ]
        session = await self._session_service.save_analysis_result(
            session.id,
            result.facts,
            questions,
            ANALYSIS_PROMPT_VERSION,
        )
        if session.status is SessionStatus.GENERATING_DIAGRAM:
            await self._generate_diagram(session)

    async def submit_answers(
        self, session_id: str, question_round: int, answers: list[Answer]
    ) -> DiagramSession:
        session = await self._session_service.get(session_id)
        self._analysis_service.validate_answers(
            [
                AnalysisQuestion(id=question.id, text=question.text, required=question.required)
                for question in session.questions
            ],
            [
                AnalysisAnswer(question_id=answer.question_id, value=answer.value)
                for answer in answers
            ],
        )
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
                    facts=session.analysis_facts,
                    answers=[
                        DiagramGenerationAnswer(question_id=answer.question_id, value=answer.value)
                        for answer in session.answers
                    ],
                )
            )
        except DiagramProviderError as error:
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
