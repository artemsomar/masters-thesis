import asyncio

import pytest

from app.modules.sessions.errors import InvalidSessionState, InvalidSessionToken
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.service import SessionService
from tests.fakes.fake_sessions import FakeSessionEventBroker, FakeSessionRepository


@pytest.mark.unit
def test_session_rejects_an_invalid_status_transition() -> None:
    async def scenario() -> None:
        service = SessionService(
            FakeSessionRepository(), FakeSessionEventBroker(), "test-pepper", 86_400
        )
        session, _ = await service.create("A booking system", "en")

        with pytest.raises(InvalidSessionState):
            await service.transition(session.id, SessionStatus.DIAGRAM_READY)

    asyncio.run(scenario())


@pytest.mark.unit
def test_session_requires_its_matching_access_token() -> None:
    async def scenario() -> None:
        service = SessionService(
            FakeSessionRepository(), FakeSessionEventBroker(), "test-pepper", 86_400
        )
        session, _ = await service.create("A booking system", "en")

        with pytest.raises(InvalidSessionToken):
            await service.get_authorized(session.id, "another-token")

    asyncio.run(scenario())
