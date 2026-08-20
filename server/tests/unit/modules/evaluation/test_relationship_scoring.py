import asyncio

import pytest

from app.modules.evaluation.dataset_reader import EvaluationDatasetReader
from app.modules.evaluation.enums import EvaluationRelationType
from app.modules.evaluation.schemas import ComparableDiagram, EvaluationNode, EvaluationRelation
from app.modules.evaluation.service import EvaluationService
from tests.fakes.fake_embeddings import FakeEmbeddingClient


@pytest.mark.unit
def test_relationship_scoring_requires_the_matched_endpoints_and_relation_type() -> None:
    async def scenario() -> None:
        service = EvaluationService(
            EvaluationDatasetReader(),
            FakeEmbeddingClient(
                {
                    "Customer": [1.0, 0.0, 0.0],
                    "Buyer": [1.0, 0.0, 0.0],
                    "Place order": [0.0, 1.0, 0.0],
                    "Create order": [0.0, 1.0, 0.0],
                    "Process payment": [0.0, 0.0, 1.0],
                    "Make payment": [0.0, 0.0, 1.0],
                }
            ),
            20_000,
            0.5,
            0.5,
        )

        _, _, relationship_scores = await service.compare(
            _reference_diagram(), _generated_diagram()
        )

        assert relationship_scores.association.f1 == 1
        assert relationship_scores.include.f1 == 0
        assert relationship_scores.extend.f1 == 0
        assert relationship_scores.overall.f1 == 0.5

    asyncio.run(scenario())


def _reference_diagram() -> ComparableDiagram:
    return ComparableDiagram(
        actors=[EvaluationNode(id="customer", name="Customer")],
        use_cases=[
            EvaluationNode(id="place-order", name="Place order"),
            EvaluationNode(id="process-payment", name="Process payment"),
        ],
        relations=[
            EvaluationRelation(
                type=EvaluationRelationType.ASSOCIATION,
                source_id="customer",
                target_id="place-order",
            ),
            EvaluationRelation(
                type=EvaluationRelationType.INCLUDE,
                source_id="place-order",
                target_id="process-payment",
            ),
        ],
    )


def _generated_diagram() -> ComparableDiagram:
    return ComparableDiagram(
        actors=[EvaluationNode(id="buyer", name="Buyer")],
        use_cases=[
            EvaluationNode(id="create-order", name="Create order"),
            EvaluationNode(id="make-payment", name="Make payment"),
        ],
        relations=[
            EvaluationRelation(
                type=EvaluationRelationType.ASSOCIATION,
                source_id="buyer",
                target_id="create-order",
            ),
            EvaluationRelation(
                type=EvaluationRelationType.EXTEND,
                source_id="create-order",
                target_id="make-payment",
            ),
        ],
    )
