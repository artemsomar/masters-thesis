import asyncio
from typing import TypeVar, cast

import pytest
from pydantic import BaseModel

from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import (
    Actor,
    Diagram,
    DiagramRelation,
    DiagramSystem,
    UseCase,
)

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.errors import SessionNotFound
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow
from tests.fakes.fake_llm import FakeStructuredLlmClient
from tests.fakes.fake_sessions import (
    FakeSessionCreationLimiter,
    FakeSessionEventBroker,
    FakeSessionJobDispatcher,
    FakeSessionRepository,
)


@pytest.mark.unit
def test_cancelled_session_cannot_store_a_generated_diagram() -> None:
    async def scenario() -> None:
        repository = FakeSessionRepository()
        event_broker = FakeSessionEventBroker()
        session_service = SessionService(
            repository,
            event_broker,
            FakeSessionCreationLimiter(),
            "test-pepper",
            86_400,
            20_000,
            2_000,
        )
        created_session = await session_service.create("A booking system", "en", "127.0.0.1")
        session = created_session.session
        await session_service.transition(session.id, SessionStatus.ANALYZING)
        workflow = DiagramSessionWorkflow(
            session_service,
            FakeSessionJobDispatcher(),
            DiagramService(CancellingStructuredLlmClient(session_service, session.id)),
        )

        with pytest.raises(SessionNotFound):
            await workflow.process_session(session.id)

        assert session.id not in repository.sessions
        assert [event.status for event in event_broker.events[session.id]] == [
            SessionStatus.ANALYZING,
            SessionStatus.GENERATING_DIAGRAM,
        ]

    asyncio.run(scenario())


class CancellingStructuredLlmClient:
    def __init__(self, session_service: SessionService, session_id: str) -> None:
        self._session_service = session_service
        self._session_id = session_id

    async def generate(self, _: str, __: type[ResponseModel], ___: str) -> ResponseModel:
        await self._session_service.delete(self._session_id)
        return cast(
            ResponseModel,
            Diagram(
                schema_version="1.0",
                system=DiagramSystem(
                    id="booking-system", name="Booking system", spans=[], origin="unverified"
                ),
                actors=[
                    Actor(
                        id="client",
                        name="Client",
                        type=ActorType.PRIMARY,
                        spans=[],
                        origin="unverified",
                    )
                ],
                use_cases=[
                    UseCase(id="book-service", name="Book service", spans=[], origin="unverified")
                ],
                relations=[
                    DiagramRelation(
                        type=RelationType.ASSOCIATION,
                        source_id="client",
                        target_id="book-service",
                        spans=[],
                        origin="unverified",
                    )
                ],
                assumptions=[],
                warnings=[],
            ),
        )
