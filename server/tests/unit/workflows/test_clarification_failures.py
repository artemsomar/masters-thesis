import asyncio

import pytest

from app.modules.clarifications.schemas import ClarificationQuestion, ClarificationResult
from app.modules.clarifications.service import ClarificationService
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
def test_invalid_clarification_result_marks_the_session_as_failed() -> None:
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
        clarification_service = ClarificationService(
            FakeStructuredLlmClient(
                ClarificationResult(
                    questions=[
                        ClarificationQuestion(
                            id=f"question-{index}", text="Clarify this requirement"
                        )
                        for index in range(8)
                    ]
                )
            ),
            max_questions_per_round=7,
        )
        workflow = DiagramSessionWorkflow(
            session_service,
            FakeSessionJobDispatcher(),
            clarification_service,
            DiagramService(
                FakeStructuredLlmClient(
                    Diagram(
                        schema_version="1.0",
                        system=DiagramSystem(id="booking-system", name="Booking system"),
                        actors=[Actor(id="client", name="Client", type=ActorType.PRIMARY)],
                        use_cases=[UseCase(id="book-service", name="Book service")],
                        relations=[
                            DiagramRelation(
                                type=RelationType.ASSOCIATION,
                                source_id="client",
                                target_id="book-service",
                            )
                        ],
                        assumptions=[],
                        warnings=[],
                    )
                )
            ),
            max_clarification_rounds=3,
        )
        session, _ = await session_service.create("A booking system", "en", "127.0.0.1")
        await session_service.transition(session.id, SessionStatus.ANALYZING)

        await workflow.process_session(session.id)

        assert (await session_service.get(session.id)).status is SessionStatus.FAILED

    asyncio.run(scenario())
