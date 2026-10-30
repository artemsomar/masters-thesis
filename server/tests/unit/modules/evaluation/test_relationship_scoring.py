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
                    _use_case_text("Place order"): [0.0, 1.0, 0.0],
                    _use_case_text("Create order"): [0.0, 1.0, 0.0],
                    _use_case_text("Process payment"): [0.0, 0.0, 1.0],
                    _use_case_text("Make payment"): [0.0, 0.0, 1.0],
                }
            ),
            20_000,
            0.5,
            0.5,
        )

        comparison = await service.compare(
            _reference_diagram(),
            _generated_diagram(),
            system_description="A customer orders products and pays for them.",
        )
        relationship_scores = comparison.relationship_scores

        assert relationship_scores.association.f1 == 1
        assert relationship_scores.include.f1 == 0
        assert relationship_scores.extend.f1 == 0
        assert relationship_scores.overall.f1 == 0.5

    asyncio.run(scenario())


@pytest.mark.unit
def test_use_case_matching_uses_the_system_description_as_embedding_context() -> None:
    async def scenario() -> None:
        description = "Customers can add products to their shopping cart before checkout."
        add_to_cart = _use_case_text_with_description(description, "Add to cart")
        delete_from_cart = _use_case_text_with_description(description, "Delete from cart")
        embeddings = FakeEmbeddingClient(
            {
                add_to_cart: [1.0, 0.0],
                delete_from_cart: [0.0, 1.0],
            }
        )
        service = EvaluationService(EvaluationDatasetReader(), embeddings, 20_000, 0.5, 0.8)

        comparison = await service.compare(
            ComparableDiagram(
                actors=[],
                use_cases=[EvaluationNode(id="add", name="Add to cart")],
                relations=[],
            ),
            ComparableDiagram(
                actors=[],
                use_cases=[EvaluationNode(id="delete", name="Delete from cart")],
                relations=[],
            ),
            system_description=description,
        )

        assert comparison.use_case_matching.mapping == {}
        assert comparison.use_case_matching.score.f1 == 0
        assert embeddings.calls == [[add_to_cart, delete_from_cart]]

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


def _use_case_text(name: str) -> str:
    return _use_case_text_with_description("A customer orders products and pays for them.", name)


def _use_case_text_with_description(description: str, name: str) -> str:
    return f"System description:\n{description}\n\nUse case:\n{name}"
