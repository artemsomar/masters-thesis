from types import SimpleNamespace

from fastapi import FastAPI

from app.main import create_app
from app.modules.clarifications.schemas import ClarificationQuestion, ClarificationResult
from app.modules.clarifications.service import ClarificationService
from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import Actor, Diagram, DiagramRelation, DiagramSystem, UseCase
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow
from tests.fakes.fake_llm import FakeStructuredLlmClient
from tests.fakes.fake_sessions import (
    FakeSessionCreationLimiter,
    FakeSessionEventBroker,
    FakeSessionJobDispatcher,
    FakeSessionRepository,
)


def create_test_app(clarification_result: ClarificationResult | None = None) -> FastAPI:
    repository = FakeSessionRepository()
    event_broker = FakeSessionEventBroker()
    service = SessionService(
        repository,
        event_broker,
        FakeSessionCreationLimiter(),
        "test-pepper",
        86_400,
        20_000,
        2_000,
    )
    clarification_llm_client = FakeStructuredLlmClient(clarification_result or _questions_result())
    clarification_service = ClarificationService(
        clarification_llm_client,
        max_questions_per_round=7,
    )
    diagram_llm_client = FakeStructuredLlmClient(
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
    diagram_service = DiagramService(diagram_llm_client)
    workflow = DiagramSessionWorkflow(
        service,
        FakeSessionJobDispatcher(),
        clarification_service,
        diagram_service,
        max_clarification_rounds=3,
    )
    app = create_app()
    app.state.container = SimpleNamespace(
        session_service=service,
        session_event_broker=event_broker,
        diagram_session_workflow=workflow,
        clarification_llm_client=clarification_llm_client,
        diagram_llm_client=diagram_llm_client,
    )
    return app


def _questions_result() -> ClarificationResult:
    return ClarificationResult(
        questions=[
            ClarificationQuestion(
                id="confirmation-channel",
                text="How is a booking confirmed?",
            )
        ],
    )
