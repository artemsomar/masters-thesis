from types import SimpleNamespace
from collections.abc import Awaitable, Callable

from fastapi import FastAPI

from app.main import create_app
from app.modules.diagrams.contracts.results import (
    DiagramQualityReport,
    FinalDiagram,
    PipelineVersions,
    RawDiagram,
)
from app.modules.diagrams.diagram_assurance import DiagramAssuranceResult
from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import Actor, Diagram, DiagramRelation, DiagramSystem, UseCase
from app.modules.diagrams.service import DiagramService
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow
from app.workflows.requirement_diagram_pipeline import RequirementDiagramPipelineResult
from tests.fakes.fake_llm import FakeStructuredLlmClient
from tests.fakes.fake_sessions import (
    FakeSessionCreationLimiter,
    FakeSessionEventBroker,
    FakeSessionJobDispatcher,
    FakeSessionRepository,
)


class PipelineStub:
    async def run(
        self,
        _: str,
        __: str,
        report_phase: Callable[[str], Awaitable[None]] | None = None,
    ) -> RequirementDiagramPipelineResult:
        if report_phase is not None:
            await report_phase("extracting_frames")
        diagram = _diagram()
        versions = PipelineVersions(
            frame_extraction_prompt="v1", defect_rules="v1", assurance_rules="v1"
        )
        return RequirementDiagramPipelineResult(
            assurance=DiagramAssuranceResult(
                raw=RawDiagram(diagram=diagram, pipeline_versions=versions),
                final=FinalDiagram(diagram=diagram, pipeline_versions=versions),
                report=DiagramQualityReport(),
            ),
            initial=diagram,
        )


def create_test_app() -> FastAPI:
    repository = FakeSessionRepository()
    event_broker = FakeSessionEventBroker()
    service = SessionService(
        repository, event_broker, FakeSessionCreationLimiter(), "test-pepper", 86_400, 20_000, 2_000
    )
    workflow = DiagramSessionWorkflow(
        service,
        FakeSessionJobDispatcher(),
        DiagramService(FakeStructuredLlmClient(_diagram())),
        PipelineStub(),  # type: ignore[arg-type]
        new_pipeline_enabled=True,
    )
    app = create_app()
    app.state.container = SimpleNamespace(
        session_service=service,
        session_event_broker=event_broker,
        diagram_session_workflow=workflow,
    )
    return app


def _diagram() -> Diagram:
    return Diagram(
        schema_version="1.0",
        system=DiagramSystem(
            id="booking-system", name="Booking system", spans=[], origin="unverified"
        ),
        actors=[
            Actor(id="client", name="Client", type=ActorType.PRIMARY, spans=[], origin="unverified")
        ],
        use_cases=[UseCase(id="book-service", name="Book service", spans=[], origin="unverified")],
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
