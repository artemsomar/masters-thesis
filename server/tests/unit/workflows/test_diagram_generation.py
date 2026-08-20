import asyncio

import pytest

from app.modules.clarifications.schemas import ClarificationResult
from app.modules.clarifications.service import ClarificationService
from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import Actor, AssociationRelation, Diagram, DiagramSystem, UseCase
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow
from tests.fakes.fake_llm import FakeStructuredLlmClient
from tests.fakes.fake_sessions import (
    FakeSessionEventBroker,
    FakeSessionCreationLimiter,
    FakeSessionJobDispatcher,
    FakeSessionRepository,
)


@pytest.mark.unit
def test_invalid_generated_diagram_marks_the_session_as_failed() -> None:
    async def scenario() -> None:
        session_service = SessionService(
            FakeSessionRepository(),
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
            ClarificationService(FakeStructuredLlmClient(ClarificationResult()), 7),
            DiagramService(FakeStructuredLlmClient(_invalid_diagram())),
            max_clarification_rounds=3,
        )
        session, _ = await session_service.create("A booking system", "en", "127.0.0.1")
        await session_service.transition(session.id, SessionStatus.ANALYZING)

        await workflow.process_session(session.id)

        failed = await session_service.get(session.id)
        assert failed.status is SessionStatus.FAILED
        assert failed.error_code == "diagram_generation_failed"

    asyncio.run(scenario())


def _invalid_diagram() -> Diagram:
    return Diagram(
        schema_version="1.0",
        system=DiagramSystem(id="booking-system", name="Booking system"),
        actors=[Actor(id="client", name="Client", type=ActorType.PRIMARY)],
        use_cases=[UseCase(id="book-service", name="Book service")],
        relations=[
            AssociationRelation(
                type=RelationType.ASSOCIATION,
                source_id="book-service",
                target_id="book-service",
            )
        ],
        assumptions=[],
        warnings=[],
    )
