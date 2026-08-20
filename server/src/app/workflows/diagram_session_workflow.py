from uuid import uuid4

from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession
from app.modules.sessions.ports import SessionJobDispatcher
from app.modules.sessions.service import SessionService


class DiagramSessionWorkflow:
    def __init__(
        self, session_service: SessionService, job_dispatcher: SessionJobDispatcher
    ) -> None:
        self._session_service = session_service
        self._job_dispatcher = job_dispatcher

    async def create_session(self, description: str, language: str) -> tuple[DiagramSession, str]:
        session, token = await self._session_service.create(description, language)
        await self._session_service.transition(session.id, SessionStatus.ANALYZING)
        job_id = str(uuid4())
        session = await self._session_service.set_current_job(session.id, job_id)
        try:
            self._job_dispatcher.dispatch_session_processing(session.id, job_id)
        except Exception:
            await self._session_service.transition(session.id, SessionStatus.FAILED)
            raise
        return session, token

    async def delete_session(self, session_id: str) -> None:
        session = await self._session_service.get(session_id)
        if session.current_job_id is not None:
            self._job_dispatcher.cancel(session.current_job_id)
        await self._session_service.delete(session_id)

    async def process_session(self, session_id: str) -> None:
        await self._session_service.get(session_id)
