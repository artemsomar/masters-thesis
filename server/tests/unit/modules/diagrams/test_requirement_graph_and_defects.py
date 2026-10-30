import asyncio

from app.modules.diagrams.contracts.corrections import CorrectionOperation, DefectType
from app.modules.diagrams.contracts.graph import RequirementEdgeType, RequirementNodeType
from app.modules.diagrams.contracts.provenance import SourceSpan
from app.modules.diagrams.contracts.requirements import RequirementFrame
from app.modules.diagrams.defect_detection import (
    DefectDetectionSettings,
    RequirementDefectDetector,
)
from app.modules.diagrams.requirement_graph import (
    RequirementGraphBuilder,
    RequirementGraphSettings,
)
from tests.fakes.fake_embeddings import FakeEmbeddingClient


def _frame(
    identifier: str,
    *,
    actor: str | None = "Customer",
    action: str | None = "book",
    object_name: str | None = "service",
    spans: list[SourceSpan] | None = None,
) -> RequirementFrame:
    return RequirementFrame(
        id=identifier,
        actor=actor,
        action=action,
        object=object_name,
        spans=spans or [],
        origin="unverified",
    )


def test_graph_reuses_normalized_terms_and_preserves_frame_traceability() -> None:
    span = SourceSpan(start_offset=0, end_offset=8, text="Customer", origin="extracted")
    graph = asyncio.run(
        RequirementGraphBuilder().build(
            [
                _frame("f1", spans=[span]),
                _frame("f2", actor=" customer ", object_name="booking", spans=[span]),
            ]
        )
    )

    actors = [node for node in graph.nodes if node.type is RequirementNodeType.ACTOR]
    performs = [edge for edge in graph.edges if edge.type is RequirementEdgeType.PERFORMS]

    assert len(actors) == 1
    assert actors[0].frame_ids == ["f1", "f2"]
    assert actors[0].spans == [span]
    assert len(performs) == 1
    assert performs[0].frame_ids == ["f1", "f2"]
    assert performs[0].spans == [span]


def test_similarity_only_compares_terms_of_the_same_type_above_threshold() -> None:
    embeddings = FakeEmbeddingClient(
        {
            "client": [1.0, 0.0],
            "customer": [0.99, 0.01],
        }
    )
    graph = asyncio.run(
        RequirementGraphBuilder(
            embeddings, RequirementGraphSettings(similarity_threshold=0.9)
        ).build([_frame("f1", actor="Client"), _frame("f2", actor="Customer")])
    )

    similar_edges = [edge for edge in graph.edges if edge.type is RequirementEdgeType.SIMILAR]

    assert len(similar_edges) == 1
    assert embeddings.calls == [["client", "customer"]]
    assert similar_edges[0].frame_ids == ["f1", "f2"]


def test_detector_reports_stable_rule_backed_defects_without_correction() -> None:
    shared_span = SourceSpan(start_offset=0, end_offset=4, text="User", origin="extracted")
    frames = [
        _frame("incomplete", actor=None, action="manage", object_name=None),
        _frame("compound-a", action="create and edit", spans=[shared_span]),
        _frame("compound-b", action="select", spans=[shared_span]),
        _frame("vague", action="manage"),
    ]
    graph = asyncio.run(RequirementGraphBuilder().build(frames))
    detector = RequirementDefectDetector(
        DefectDetectionSettings(
            vague_verbs=frozenset({"manage"}), action_step_verbs=frozenset({"select"})
        )
    )

    first = detector.detect(frames, graph)
    second = detector.detect(frames, graph)

    assert first == second
    assert [(defect.type, defect.assigned_operation) for defect in first] == [
        (DefectType.ACTION_STEP, CorrectionOperation.MERGE_STEPS),
        (DefectType.COMPOUND_STATEMENT, CorrectionOperation.SPLIT),
        (DefectType.COMPOUND_STATEMENT, CorrectionOperation.SPLIT),
        (DefectType.INCOMPLETE_FRAME, CorrectionOperation.RESOLVE),
        (DefectType.VAGUE_VERB, CorrectionOperation.SPECIFY),
        (DefectType.VAGUE_VERB, CorrectionOperation.SPECIFY),
    ]
    assert {defect.id for defect in first if defect.type is DefectType.COMPOUND_STATEMENT} == {
        "compound-action-compound-a",
        next(defect.id for defect in first if defect.id.startswith("compound-span-")),
    }


def test_similarity_edge_becomes_a_terminology_defect_for_actors() -> None:
    embeddings = FakeEmbeddingClient({"client": [1.0, 0.0], "customer": [1.0, 0.0]})
    frames = [_frame("f1", actor="Client"), _frame("f2", actor="Customer")]
    graph = asyncio.run(RequirementGraphBuilder(embeddings).build(frames))

    defects = RequirementDefectDetector().detect(frames, graph)
    terminology = [
        defect for defect in defects if defect.type is DefectType.INCONSISTENT_TERMINOLOGY
    ]

    assert len(terminology) == 1
    assert terminology[0].assigned_operation is CorrectionOperation.UNIFY
    assert terminology[0].frame_ids == ["f1", "f2"]
