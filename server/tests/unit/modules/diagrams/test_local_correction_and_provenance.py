import asyncio

import pytest

from app.infrastructure.llm.client import InvalidStructuredOutputError, LlmProviderError
from app.modules.diagrams.contracts.corrections import (
    CorrectionOperation,
    CorrectionProposal,
    DefectType,
    DetectedDefect,
    ProvenanceDecisionStatus,
)
from app.modules.diagrams.contracts.provenance import SourceSpan
from app.modules.diagrams.contracts.requirements import RequirementFrame
from app.modules.diagrams.local_correction import LocalCorrectionService
from app.modules.diagrams.provenance_gate import ProvenanceGate
from app.modules.diagrams.requirement_graph import RequirementGraphBuilder
from tests.fakes.fake_llm import FakeStructuredLlmClient


DESCRIPTION = "Customer manages an account."
SPAN = SourceSpan(start_offset=0, end_offset=len(DESCRIPTION), text=DESCRIPTION, origin="extracted")


@pytest.mark.parametrize(
    ("operation", "input_count", "proposed_count"),
    [
        (CorrectionOperation.RESOLVE, 1, 1),
        (CorrectionOperation.SPLIT, 1, 2),
        (CorrectionOperation.SPECIFY, 1, 1),
        (CorrectionOperation.UNIFY, 2, 2),
        (CorrectionOperation.MERGE_STEPS, 2, 1),
    ],
)
def test_gate_accepts_every_allowed_operation_shape(
    operation: CorrectionOperation, input_count: int, proposed_count: int
) -> None:
    inputs = [_frame(f"f{index}") for index in range(input_count)]
    defect = _defect(operation, [frame.id for frame in inputs])
    proposal = CorrectionProposal(
        id=f"proposal-{operation.value.lower().replace('_', '-')}",
        defect_id=defect.id,
        operation=operation,
        input_frame_ids=[frame.id for frame in inputs],
        proposed_frames=[_frame(f"result-{index}") for index in range(proposed_count)],
    )

    result = ProvenanceGate().evaluate(proposal, defect, inputs, DESCRIPTION)

    assert result.accepted is True
    assert result.frames == proposal.proposed_frames
    assert result.decision.status is ProvenanceDecisionStatus.ACCEPTED


def test_gate_rejects_the_entire_proposal_when_one_new_element_has_no_provenance() -> None:
    input_frame = _frame("f1")
    defect = _defect(CorrectionOperation.SPLIT, [input_frame.id])
    proposal = CorrectionProposal(
        id="proposal-split",
        defect_id=defect.id,
        operation=CorrectionOperation.SPLIT,
        input_frame_ids=[input_frame.id],
        proposed_frames=[
            _frame("result-one"),
            _frame("result-two", origin="unverified", spans=[]),
        ],
    )

    result = ProvenanceGate().evaluate(proposal, defect, [input_frame], DESCRIPTION)

    assert result.accepted is False
    assert result.frames == [input_frame]
    assert result.decision.status is ProvenanceDecisionStatus.REJECTED
    assert result.decision.verified_spans == []


def test_gate_accepts_a_derived_result_with_a_verified_input_chain() -> None:
    input_frame = _frame("f1")
    defect = _defect(CorrectionOperation.RESOLVE, [input_frame.id])
    proposal = CorrectionProposal(
        id="proposal-resolve",
        defect_id=defect.id,
        operation=CorrectionOperation.RESOLVE,
        input_frame_ids=[input_frame.id],
        proposed_frames=[_frame("result", origin="derived:f1", spans=[])],
    )

    result = ProvenanceGate().evaluate(proposal, defect, [input_frame], DESCRIPTION)

    assert result.accepted is True
    assert result.decision.checks[-1].passed is True


def test_local_correction_receives_only_the_local_evidence_not_the_full_description() -> None:
    input_frame = _frame("f1")
    defect = _defect(CorrectionOperation.SPECIFY, [input_frame.id])
    proposal = CorrectionProposal(
        id="proposal-specify",
        defect_id=defect.id,
        operation=CorrectionOperation.SPECIFY,
        input_frame_ids=[input_frame.id],
        proposed_frames=[_frame("result")],
    )
    client = FakeStructuredLlmClient(proposal)
    graph = asyncio.run(RequirementGraphBuilder().build([input_frame]))

    result = asyncio.run(
        LocalCorrectionService(client).correct(
            defect, [input_frame], graph, DESCRIPTION + " This sentence is unavailable."
        )
    )

    assert result.gate_result.accepted is True
    assert DESCRIPTION + " This sentence is unavailable." not in client.calls[0][0]
    assert SPAN.text in client.calls[0][0]


def test_local_correction_keeps_original_frames_when_both_responses_are_invalid() -> None:
    frame = _frame("f1")
    defect = _defect(CorrectionOperation.SPECIFY, [frame.id])
    graph = asyncio.run(RequirementGraphBuilder().build([frame]))

    client = FakeStructuredLlmClient(InvalidStructuredOutputError())
    result = asyncio.run(
        LocalCorrectionService(client).correct(defect, [frame], graph, DESCRIPTION)
    )

    assert len(client.calls) == 2
    assert result.frames == [frame]
    assert result.gate_result.accepted is False
    assert result.gate_result.decision.status is ProvenanceDecisionStatus.REJECTED
    assert result.gate_result.decision.checks[0].name == "structured_output"
    assert result.gate_result.decision.verified_spans == []
    assert "previous response failed schema validation" in client.calls[1][0]


def test_local_correction_accepts_valid_retry_through_provenance_gate() -> None:
    from unittest.mock import AsyncMock, patch

    frame = _frame("f1")
    defect = _defect(CorrectionOperation.SPECIFY, [frame.id])
    proposal = CorrectionProposal(
        id="proposal-retry",
        defect_id=defect.id,
        operation=defect.assigned_operation,
        input_frame_ids=[frame.id],
        proposed_frames=[_frame("result")],
    )
    client = FakeStructuredLlmClient(proposal)
    graph = asyncio.run(RequirementGraphBuilder().build([frame]))
    generate = AsyncMock(side_effect=[InvalidStructuredOutputError(), proposal])
    with patch.object(client, "generate", generate):
        result = asyncio.run(
            LocalCorrectionService(client).correct(defect, [frame], graph, DESCRIPTION)
        )

    assert generate.await_count == 2
    assert result.gate_result.accepted is True
    assert result.frames == proposal.proposed_frames


def test_local_correction_preserves_provider_error_for_job_retry() -> None:
    frame = _frame("f1")
    defect = _defect(CorrectionOperation.SPECIFY, [frame.id])
    graph = asyncio.run(RequirementGraphBuilder().build([frame]))
    with pytest.raises(LlmProviderError):
        asyncio.run(
            LocalCorrectionService(
                FakeStructuredLlmClient(LlmProviderError(retryable=True))
            ).correct(defect, [frame], graph, DESCRIPTION)
        )


def _frame(
    identifier: str,
    *,
    origin: str = "extracted",
    spans: list[SourceSpan] | None = None,
) -> RequirementFrame:
    return RequirementFrame(
        id=identifier,
        actor="Customer",
        action="manages",
        object="account",
        spans=[SPAN] if spans is None else spans,
        origin=origin,
    )


def _defect(operation: CorrectionOperation, frame_ids: list[str]) -> DetectedDefect:
    return DetectedDefect(
        id=f"defect-{operation.value.lower().replace('_', '-')}",
        type=DefectType.VAGUE_VERB,
        frame_ids=frame_ids,
        evidence="A stable local rule detected this defect.",
        assigned_operation=operation,
    )
