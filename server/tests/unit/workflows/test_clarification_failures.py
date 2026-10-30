import asyncio

import pytest

from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import Actor, Diagram, DiagramRelation, DiagramSystem, UseCase
from app.modules.diagrams.service import DiagramService
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
def test_noninteractive_workflow_generates_a_diagram() -> None:
    async def scenario() -> None:
        repository = FakeSessionRepository()
        session_service = SessionService(
            repository,
            FakeSessionEventBroker(),
            FakeSessionCreationLimiter(),
            "test-pepper",
            86_400,
            20_000,
            2_000,
        )
        workflow = DiagramSessionWorkflow(
            session_service,
            FakeSessionJobDispatcher(),
            DiagramService(
                FakeStructuredLlmClient(
                    Diagram(
                        schema_version="1.0",
                        system=DiagramSystem(
                            id="booking-system",
                            name="Booking system",
                            spans=[],
                            origin="unverified",
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
                            UseCase(
                                id="book-service",
                                name="Book service",
                                spans=[],
                                origin="unverified",
                            )
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
                    )
                )
            ),
        )
        created_session = await session_service.create("A booking system", "en", "127.0.0.1")
        session = created_session.session
        await session_service.transition(session.id, SessionStatus.ANALYZING)

        await workflow.process_session(session.id)

        assert (await session_service.get(session.id)).status is SessionStatus.DIAGRAM_READY

    asyncio.run(scenario())
