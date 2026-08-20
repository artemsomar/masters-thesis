from types import SimpleNamespace

from fastapi import FastAPI

from app.main import create_app
from app.modules.analysis.schemas import AnalysisQuestion, AnalysisResult
from app.modules.analysis.service import RequirementsAnalysisService
from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import Actor, AssociationRelation, Diagram, DiagramSystem, UseCase
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow
from tests.fakes.fake_sessions import (
    FakeDiagramGenerator,
    FakeRequirementsAnalyzer,
    FakeSessionCreationLimiter,
    FakeSessionEventBroker,
    FakeSessionJobDispatcher,
    FakeSessionRepository,
)


def create_test_app(analysis_result: AnalysisResult | None = None) -> FastAPI:
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
    analysis_service = RequirementsAnalysisService(
        FakeRequirementsAnalyzer(analysis_result or _questions_result()),
        max_questions_per_round=7,
    )
    diagram_service = DiagramService(
        FakeDiagramGenerator(
            Diagram(
                schema_version="1.0",
                system=DiagramSystem(id="booking-system", name="Booking system"),
                actors=[Actor(id="client", name="Client", type=ActorType.PRIMARY)],
                use_cases=[UseCase(id="book-service", name="Book service")],
                relations=[
                    AssociationRelation(
                        type=RelationType.ASSOCIATION,
                        source_id="client",
                        target_id="book-service",
                    )
                ],
                assumptions=[],
                warnings=[],
            )
        )
    )
    workflow = DiagramSessionWorkflow(
        service,
        FakeSessionJobDispatcher(),
        analysis_service,
        diagram_service,
        max_analysis_rounds=3,
    )
    app = create_app()
    app.state.container = SimpleNamespace(
        session_service=service,
        session_event_broker=event_broker,
        diagram_session_workflow=workflow,
    )
    return app


def _questions_result() -> AnalysisResult:
    return AnalysisResult(
        facts=["The system has a booking flow"],
        questions=[
            AnalysisQuestion(
                id="confirmation-channel",
                text="How is a booking confirmed?",
            )
        ],
    )
