from collections.abc import AsyncIterator
from typing import Protocol

from app.modules.sessions.schemas import SessionStatusUpdate


class SessionEventPublisher(Protocol):
    async def publish_status(self, session_id: str, event: SessionStatusUpdate) -> None: ...


class SessionEventSubscriber(Protocol):
    def subscribe_statuses(self, session_id: str) -> AsyncIterator[SessionStatusUpdate | None]: ...


class SessionJobDispatcher(Protocol):
    def dispatch_session_processing(self, session_id: str, job_id: str) -> None: ...

    def cancel(self, job_id: str) -> None: ...


class SessionCreationLimiter(Protocol):
    async def acquire(self, session_id: str, client_fingerprint: str) -> None: ...

    async def release(self, session_id: str) -> None: ...
