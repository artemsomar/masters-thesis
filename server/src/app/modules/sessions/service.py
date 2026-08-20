import hmac
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.sessions.errors import (
    InvalidQuestionRound,
    InvalidSessionState,
    InvalidSessionToken,
    QuestionsNotAvailable,
    SessionNotFound,
)
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession
from app.modules.sessions.ports import SessionCreationLimiter, SessionEventPublisher
from app.modules.sessions.repository import SessionRepository
from app.modules.sessions.input_validation import validate_answers, validate_description
from app.modules.sessions.schemas import Answer, Question
from app.modules.sessions.state_machine import is_allowed
from app.modules.sessions.status_events import publish_status
from app.modules.sessions.tokens import create_token, hash_token


class SessionService:
    def __init__(
        self,
        repository: SessionRepository,
        event_publisher: SessionEventPublisher,
        creation_limiter: SessionCreationLimiter,
        token_pepper: str,
        ttl_seconds: int,
        max_description_length: int,
        max_answer_length: int,
    ) -> None:
        self._repository = repository
        self._event_publisher = event_publisher
        self._creation_limiter = creation_limiter
        self._token_pepper = token_pepper
        self._ttl = timedelta(seconds=ttl_seconds)
        self._max_description_length = max_description_length
        self._max_answer_length = max_answer_length

    async def create(
        self, description: str, language: str, client_address: str
    ) -> tuple[DiagramSession, str]:
        validate_description(description, self._max_description_length)
        token = create_token()
        now = datetime.now(UTC)
        session = DiagramSession(
            id=str(uuid4()),
            token_hash=hash_token(token, self._token_pepper),
            description=description,
            language=language,
            status=SessionStatus.CREATED,
            created_at=now,
            updated_at=now,
            expires_at=now + self._ttl,
        )
        await self._creation_limiter.acquire(
            session.id, hash_token(client_address, self._token_pepper)
        )
        try:
            await self._repository.save(session)
        except Exception:
            await self._creation_limiter.release(session.id)
            raise
        return session, token

    async def get_authorized(self, session_id: str, token: str) -> DiagramSession:
        session = await self._get(session_id)
        if not hmac.compare_digest(session.token_hash, hash_token(token, self._token_pepper)):
            raise InvalidSessionToken()
        return session

    async def get(self, session_id: str) -> DiagramSession:
        return await self._get(session_id)

    async def transition(self, session_id: str, target: SessionStatus) -> DiagramSession:
        session = await self._get(session_id)
        if not is_allowed(session.status, target):
            raise InvalidSessionState()
        session.status = target
        self._touch(session)
        await self._repository.save(session)
        await self._publish_status(session)
        return session

    async def set_current_job(self, session_id: str, job_id: str) -> DiagramSession:
        session = await self._get(session_id)
        session.current_job_id = job_id
        self._touch(session)
        await self._repository.save(session)
        return session

    async def save_analysis_result(
        self,
        session_id: str,
        facts: list[str],
        questions: list[Question],
        prompt_version: str,
    ) -> DiagramSession:
        session = await self._get(session_id)
        target = SessionStatus.AWAITING_ANSWERS if questions else SessionStatus.GENERATING_DIAGRAM
        status_changed = session.status is not target
        if status_changed and not is_allowed(session.status, target):
            raise InvalidSessionState()
        session.analysis_facts = facts
        session.analysis_prompt_version = prompt_version
        session.questions = questions
        if questions:
            session.question_round += 1
        if status_changed:
            session.status = target
        self._touch(session)
        await self._repository.save(session)
        if status_changed:
            await self._publish_status(session)
        return session

    async def get_questions(self, session_id: str) -> tuple[int, list[Question]]:
        session = await self._get(session_id)
        if session.status is not SessionStatus.AWAITING_ANSWERS:
            raise QuestionsNotAvailable()
        return session.question_round, session.questions

    async def submit_answers(
        self, session_id: str, question_round: int, answers: list[Answer]
    ) -> DiagramSession:
        session = await self._get(session_id)
        if session.status is not SessionStatus.AWAITING_ANSWERS:
            raise QuestionsNotAvailable()
        if session.question_round != question_round:
            raise InvalidQuestionRound()
        validate_answers(answers, self._max_answer_length)
        session.answers.extend(answers)
        session.questions = []
        session.status = SessionStatus.GENERATING_DIAGRAM
        self._touch(session)
        await self._repository.save(session)
        await self._publish_status(session)
        return session

    async def save_diagram(
        self, session_id: str, diagram_json: str, prompt_version: str
    ) -> DiagramSession:
        session = await self._get(session_id)
        if not is_allowed(session.status, SessionStatus.DIAGRAM_READY):
            raise InvalidSessionState()
        session.diagram_json = diagram_json
        session.diagram_prompt_version = prompt_version
        session.status = SessionStatus.DIAGRAM_READY
        self._touch(session)
        await self._repository.save(session)
        await self._publish_status(session)
        return session

    async def fail(self, session_id: str, error_code: str) -> DiagramSession:
        session = await self._get(session_id)
        if not is_allowed(session.status, SessionStatus.FAILED):
            raise InvalidSessionState()
        session.error_code = error_code
        session.status = SessionStatus.FAILED
        self._touch(session)
        await self._repository.save(session)
        await self._publish_status(session)
        return session

    async def delete(self, session_id: str) -> DiagramSession:
        session = await self._get(session_id)
        await self._repository.delete(session.id)
        await self._creation_limiter.release(session.id)
        return session

    async def _get(self, session_id: str) -> DiagramSession:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFound()
        return session

    def _touch(self, session: DiagramSession) -> None:
        now = datetime.now(UTC)
        session.updated_at = now
        session.expires_at = now + self._ttl

    async def _publish_status(self, session: DiagramSession) -> None:
        await publish_status(self._event_publisher, session)
