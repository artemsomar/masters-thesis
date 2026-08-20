from collections.abc import AsyncIterator
from typing import Protocol

from app.modules.sessions.enums import SessionStatus


class SessionEventPublisher(Protocol):
    async def publish_status(self, session_id: str, status: SessionStatus) -> None: ...


class SessionEventSubscriber(Protocol):
    def subscribe_statuses(self, session_id: str) -> AsyncIterator[SessionStatus | None]: ...


class SessionJobDispatcher(Protocol):
    def dispatch_session_processing(self, session_id: str, job_id: str) -> None: ...

    def cancel(self, job_id: str) -> None: ...
