from typing import Protocol

from app.modules.sessions.models import DiagramSession


class SessionRepository(Protocol):
    async def get(self, session_id: str) -> DiagramSession | None: ...

    async def save(self, session: DiagramSession) -> None: ...

    async def delete(self, session_id: str) -> None: ...
