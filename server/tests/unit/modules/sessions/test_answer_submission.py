import asyncio

import pytest

from app.modules.sessions.errors import InvalidAnswers
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.schemas import Answer, Question
from app.modules.sessions.service import SessionService
from tests.fakes.fake_sessions import (
    FakeSessionCreationLimiter,
    FakeSessionEventBroker,
    FakeSessionRepository,
)


@pytest.mark.unit
def test_answers_must_match_the_current_questions() -> None:
    async def scenario() -> None:
        service = SessionService(
            FakeSessionRepository(),
            FakeSessionEventBroker(),
            FakeSessionCreationLimiter(),
            "test-pepper",
            86_400,
            20_000,
            2_000,
        )
        session, _ = await service.create("A booking system", "en", "127.0.0.1")
        await service.transition(session.id, SessionStatus.ANALYZING)
        await service.save_clarification_result(
            session.id,
            [Question(id="booking-channel", text="How is booking confirmed?")],
            "1.0",
        )

        with pytest.raises(InvalidAnswers):
            await service.submit_answers(
                session.id,
                question_round=1,
                answers=[Answer(question_id="unknown", value="By email")],
            )

    asyncio.run(scenario())
