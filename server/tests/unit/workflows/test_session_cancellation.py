import asyncio

import pytest

from app.modules.analysis.schemas import AnalysisResult
from app.modules.analysis.service import RequirementsAnalysisService
from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import (
    Actor,
    AssociationRelation,
    Diagram,
    DiagramGenerationRequest,
    DiagramSystem,
    UseCase,
)
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.errors import SessionNotFound
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow
from tests.fakes.fake_sessions import (
    FakeRequirementsAnalyzer,
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
        session, _ = await session_service.create("A booking system", "en", "127.0.0.1")
        await session_service.transition(session.id, SessionStatus.ANALYZING)
        workflow = DiagramSessionWorkflow(
            session_service,
            FakeSessionJobDispatcher(),
            RequirementsAnalysisService(FakeRequirementsAnalyzer(AnalysisResult()), 7),
            DiagramService(CancellingDiagramGenerator(session_service, session.id)),
            max_analysis_rounds=3,
        )

        with pytest.raises(SessionNotFound):
            await workflow.process_session(session.id)

        assert session.id not in repository.sessions
        assert [event.status for event in event_broker.events[session.id]] == [
            SessionStatus.ANALYZING,
            SessionStatus.GENERATING_DIAGRAM,
        ]

    asyncio.run(scenario())


class CancellingDiagramGenerator:
    def __init__(self, session_service: SessionService, session_id: str) -> None:
        self._session_service = session_service
        self._session_id = session_id

    async def generate(self, _: DiagramGenerationRequest) -> Diagram:
        await self._session_service.delete(self._session_id)
        return Diagram(
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
