import json
from datetime import datetime

from redis.asyncio import Redis

from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession


class RedisSessionRepository:
    def __init__(self, client: Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    async def get(self, session_id: str) -> DiagramSession | None:
        value = await self._client.get(self._key(session_id))
        if value is None:
            return None
        return self._deserialize(value)

    async def save(self, session: DiagramSession) -> None:
        await self._client.set(
            self._key(session.id), self._serialize(session), ex=self._ttl_seconds
        )

    async def delete(self, session_id: str) -> None:
        await self._client.delete(self._key(session_id))

    def _key(self, session_id: str) -> str:
        return f"diagram-session:{session_id}"

    def _serialize(self, session: DiagramSession) -> str:
        return json.dumps(
            {
                "sessionId": session.id,
                "tokenHash": session.token_hash,
                "description": session.description,
                "language": session.language,
                "status": session.status,
                "currentJobId": session.current_job_id,
                "createdAt": session.created_at.isoformat(),
                "updatedAt": session.updated_at.isoformat(),
                "expiresAt": session.expires_at.isoformat(),
            }
        )

    def _deserialize(self, value: bytes | str) -> DiagramSession:
        payload = json.loads(value)
        return DiagramSession(
            id=payload["sessionId"],
            token_hash=payload["tokenHash"],
            description=payload["description"],
            language=payload["language"],
            status=SessionStatus(payload["status"]),
            current_job_id=payload["currentJobId"],
            created_at=datetime.fromisoformat(payload["createdAt"]),
            updated_at=datetime.fromisoformat(payload["updatedAt"]),
            expires_at=datetime.fromisoformat(payload["expiresAt"]),
        )
