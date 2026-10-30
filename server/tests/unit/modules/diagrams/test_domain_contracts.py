import pytest
from pydantic import ValidationError

from app.modules.diagrams.contracts.corrections import (
    CorrectionOperation,
    DefectType,
    DetectedDefect,
)
from app.modules.diagrams.contracts.graph import (
    RequirementEdgeType,
    RequirementGraph,
    RequirementGraphEdge,
    RequirementGraphNode,
    RequirementNodeType,
)
from app.modules.diagrams.contracts.provenance import SourceSpan, validate_source_spans
from app.modules.diagrams.contracts.requirements import RequirementFrame
from app.modules.diagrams.enums import ActorType
from app.modules.diagrams.schemas import Actor


def test_source_spans_must_match_the_original_description() -> None:
    description = "Customer books a service"
    span = SourceSpan(
        start_offset=0,
        end_offset=8,
        text="Customer",
        origin="extracted",
    )

    validate_source_spans(description, [span])


@pytest.mark.parametrize(
    ("span", "message"),
    [
        (
            SourceSpan(start_offset=0, end_offset=9, text="Customer", origin="extracted"),
            "text does not match",
        ),
        (
            SourceSpan(start_offset=0, end_offset=40, text="Customer", origin="extracted"),
            "offsets are outside",
        ),
    ],
)
def test_source_spans_reject_invalid_offsets_or_text(span: SourceSpan, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_source_spans("Customer books a service", [span])


def test_public_diagram_elements_require_explicit_provenance() -> None:
    with pytest.raises(ValidationError):
        Actor.model_validate({"id": "customer", "name": "Customer", "type": ActorType.PRIMARY})

    actor = Actor(
        id="customer",
        name="Customer",
        type=ActorType.PRIMARY,
        spans=[],
        origin="unverified",
    )

    assert actor.model_dump() == {
        "spans": [],
        "origin": "unverified",
        "id": "customer",
        "name": "Customer",
        "type": "primary",
    }


def test_requirement_graph_references_only_known_nodes_and_serializes() -> None:
    frame = RequirementFrame(
        id="f1",
        actor="Customer",
        action="book",
        object="service",
        spans=[],
        origin="unverified",
    )
    graph = RequirementGraph(
        nodes=[
            RequirementGraphNode(
                id="customer",
                type=RequirementNodeType.ACTOR,
                label="Customer",
                frame_ids=[frame.id],
                spans=[],
                origin="unverified",
            ),
            RequirementGraphNode(
                id="book",
                type=RequirementNodeType.ACTION,
                label="book",
                frame_ids=[frame.id],
                spans=[],
                origin="unverified",
            ),
        ],
        edges=[
            RequirementGraphEdge(
                type=RequirementEdgeType.PERFORMS,
                source_id="customer",
                target_id="book",
                spans=[],
                origin="unverified",
            )
        ],
    )

    defect = DetectedDefect(
        id="missing-object",
        type=DefectType.INCOMPLETE_FRAME,
        frame_ids=[frame.id],
        evidence="The frame has no target object.",
        assigned_operation=CorrectionOperation.RESOLVE,
    )

    assert graph.model_dump_json(by_alias=True)
    assert defect.assigned_operation is CorrectionOperation.RESOLVE


def test_requirement_graph_rejects_unknown_edge_endpoints() -> None:
    with pytest.raises(ValidationError, match="must reference existing nodes"):
        RequirementGraph(
            nodes=[],
            edges=[
                RequirementGraphEdge(
                    type=RequirementEdgeType.PERFORMS,
                    source_id="customer",
                    target_id="book",
                    spans=[],
                    origin="unverified",
                )
            ],
        )
