from collections.abc import AsyncIterator

from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession


class FakeSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[str, DiagramSession] = {}

    async def get(self, session_id: str) -> DiagramSession | None:
        return self.sessions.get(session_id)

    async def save(self, session: DiagramSession) -> None:
        self.sessions[session.id] = session

    async def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)


class FakeSessionEventBroker:
    def __init__(self) -> None:
        self.events: dict[str, list[SessionStatus]] = {}

    async def publish_status(self, session_id: str, status: SessionStatus) -> None:
        self.events.setdefault(session_id, []).append(status)

    async def subscribe_statuses(self, session_id: str) -> AsyncIterator[SessionStatus | None]:
        for event in self.events.get(session_id, []):
            yield event


class FakeSessionJobDispatcher:
    def __init__(self) -> None:
        self.dispatched: list[tuple[str, str]] = []
        self.cancelled: list[str] = []

    def dispatch_session_processing(self, session_id: str, job_id: str) -> None:
        self.dispatched.append((session_id, job_id))

    def cancel(self, job_id: str) -> None:
        self.cancelled.append(job_id)
