import asyncio

import pytest

from app.modules.diagrams.enums import ActorType, RelationType
from app.modules.diagrams.schemas import Actor, Diagram, DiagramRelation, DiagramSystem, UseCase
from app.modules.diagrams.service import DiagramService
from app.modules.evaluation.dataset_reader import EvaluationDatasetReader
from app.modules.evaluation.service import EvaluationService
from app.modules.evaluation.schemas import ComparableDiagram, EvaluationCase, EvaluationNode
from app.workflows.evaluation_workflow import EvaluationWorkflow
from tests.fakes.fake_embeddings import FakeEmbeddingClient
from tests.fakes.fake_llm import FakeStructuredLlmClient


@pytest.mark.unit
def test_evaluation_generation_does_not_include_the_reference_diagram_in_the_prompt() -> None:
    async def scenario() -> None:
        client = FakeStructuredLlmClient(_diagram())
        reference_marker = "reference-only-marker"
        evaluation_service = EvaluationService(
            EvaluationDatasetReader(),
            FakeEmbeddingClient(
                {
                    "Client": [1.0, 0.0],
                    _use_case_text("A client books a service.", "Book service"): [0.0, 1.0],
                    _use_case_text("A client books a service.", reference_marker): [0.0, 1.0],
                }
            ),
            20_000,
            0.5,
            0.5,
        )
        workflow = EvaluationWorkflow(DiagramService(client), evaluation_service)

        result = await workflow.evaluate_case(
            EvaluationCase(
                case_id="case-1",
                description="A client books a service.",
                language="en",
                reference_diagram=ComparableDiagram(
                    actors=[EvaluationNode(id="client", name="Client")],
                    use_cases=[EvaluationNode(id="reference-use-case", name=reference_marker)],
                    relations=[],
                ),
            )
        )

        assert result.case_id == "case-1"
        assert reference_marker not in client.calls[0][0]

    asyncio.run(scenario())


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


def _use_case_text(description: str, name: str) -> str:
    return f"System description:\n{description}\n\nUse case:\n{name}"
