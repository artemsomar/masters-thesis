import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.sessions.errors import InvalidSessionState, InvalidSessionToken, SessionNotFound
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession
from app.modules.sessions.ports import SessionEventPublisher
from app.modules.sessions.repository import SessionRepository
from app.modules.sessions.state_machine import is_allowed


class SessionService:
    def __init__(
        self,
        repository: SessionRepository,
        event_publisher: SessionEventPublisher,
        token_pepper: str,
        ttl_seconds: int,
    ) -> None:
        self._repository = repository
        self._event_publisher = event_publisher
        self._token_pepper = token_pepper.encode()
        self._ttl = timedelta(seconds=ttl_seconds)

    async def create(self, description: str, language: str) -> tuple[DiagramSession, str]:
        token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        session = DiagramSession(
            id=str(uuid4()),
            token_hash=self._hash_token(token),
            description=description,
            language=language,
            status=SessionStatus.CREATED,
            created_at=now,
            updated_at=now,
            expires_at=now + self._ttl,
        )
        await self._repository.save(session)
        return session, token

    async def get_authorized(self, session_id: str, token: str) -> DiagramSession:
        session = await self._get(session_id)
        if not hmac.compare_digest(session.token_hash, self._hash_token(token)):
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
        await self._event_publisher.publish_status(session.id, session.status)
        return session

    async def set_current_job(self, session_id: str, job_id: str) -> DiagramSession:
        session = await self._get(session_id)
        session.current_job_id = job_id
        self._touch(session)
        await self._repository.save(session)
        return session

    async def delete(self, session_id: str) -> DiagramSession:
        session = await self._get(session_id)
        await self._repository.delete(session.id)
        return session

    async def _get(self, session_id: str) -> DiagramSession:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFound()
        return session

    def _hash_token(self, token: str) -> str:
        return hmac.new(self._token_pepper, token.encode(), hashlib.sha256).hexdigest()

    def _touch(self, session: DiagramSession) -> None:
        now = datetime.now(UTC)
        session.updated_at = now
        session.expires_at = now + self._ttl
