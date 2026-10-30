from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.modules.diagrams.contracts.corrections import (
    CorrectionOperation,
    CorrectionProposal,
    DetectedDefect,
    ProvenanceCheck,
    ProvenanceDecision,
    ProvenanceDecisionStatus,
)
from app.modules.diagrams.contracts.provenance import SourceSpan, validate_source_spans
from app.modules.diagrams.contracts.requirements import RequirementFrame


@dataclass(frozen=True, slots=True)
class ProvenanceGateResult:
    accepted: bool
    frames: list[RequirementFrame]
    decision: ProvenanceDecision


class ProvenanceGate:
    """Accepts a whole local correction delta or rolls it back as a whole."""

    def evaluate(
        self,
        proposal: CorrectionProposal,
        defect: DetectedDefect,
        input_frames: list[RequirementFrame],
        description: str,
    ) -> ProvenanceGateResult:
        checks = [
            self._assigned_defect_check(proposal, defect),
            self._locality_check(proposal, defect),
            self._operation_invariant_check(proposal, input_frames),
            self._explicit_provenance_check(proposal, description),
            self._derived_provenance_check(proposal, input_frames, description),
        ]
        failed = next((check for check in checks if not check.passed), None)
        verified_spans = _unique_spans(
            span for frame in proposal.proposed_frames for span in frame.spans
        )
        decision = ProvenanceDecision(
            proposal_id=proposal.id,
            defect_id=defect.id,
            status=(
                ProvenanceDecisionStatus.ACCEPTED
                if failed is None
                else ProvenanceDecisionStatus.REJECTED
            ),
            reason=(
                "All local correction and provenance checks passed."
                if failed is None
                else failed.detail
            ),
            checks=checks,
            verified_spans=verified_spans if failed is None else [],
        )
        return ProvenanceGateResult(
            accepted=failed is None,
            frames=proposal.proposed_frames if failed is None else input_frames,
            decision=decision,
        )

    @staticmethod
    def _assigned_defect_check(
        proposal: CorrectionProposal, defect: DetectedDefect
    ) -> ProvenanceCheck:
        passed = proposal.defect_id == defect.id and proposal.operation is defect.assigned_operation
        return ProvenanceCheck(
            name="assigned_defect",
            passed=passed,
            detail=(
                "Proposal addresses its assigned defect and operation."
                if passed
                else "Proposal changed the assigned defect or correction operation."
            ),
        )

    @staticmethod
    def _locality_check(proposal: CorrectionProposal, defect: DetectedDefect) -> ProvenanceCheck:
        passed = set(proposal.input_frame_ids) == set(defect.frame_ids)
        return ProvenanceCheck(
            name="local_delta",
            passed=passed,
            detail=(
                "Proposal is limited to the frames referenced by the defect."
                if passed
                else "Proposal references frames outside the diagnosed local defect."
            ),
        )

    @staticmethod
    def _operation_invariant_check(
        proposal: CorrectionProposal, input_frames: list[RequirementFrame]
    ) -> ProvenanceCheck:
        inputs = {frame.id: frame for frame in input_frames}
        proposed_ids = [frame.id for frame in proposal.proposed_frames]
        unique_ids = len(proposed_ids) == len(set(proposed_ids))
        expected_inputs = set(proposal.input_frame_ids)
        known_inputs = expected_inputs == set(inputs)
        passed = unique_ids and known_inputs
        if passed and proposal.operation in {
            CorrectionOperation.RESOLVE,
            CorrectionOperation.SPECIFY,
        }:
            passed = len(proposal.proposed_frames) == 1 and len(input_frames) == 1
        if passed and proposal.operation is CorrectionOperation.SPLIT:
            passed = len(proposal.proposed_frames) >= 2
        if passed and proposal.operation is CorrectionOperation.UNIFY:
            passed = len(proposal.proposed_frames) == len(input_frames)
        if passed and proposal.operation is CorrectionOperation.MERGE_STEPS:
            passed = bool(proposal.proposed_frames)
        return ProvenanceCheck(
            name="operation_invariants",
            passed=passed,
            detail=(
                "Proposal satisfies the local operation invariants."
                if passed
                else "Proposal violates the expected shape of its local correction operation."
            ),
        )

    @staticmethod
    def _explicit_provenance_check(
        proposal: CorrectionProposal, description: str
    ) -> ProvenanceCheck:
        try:
            for frame in proposal.proposed_frames:
                if frame.origin == "unverified":
                    raise ValueError("A correction cannot introduce an unverified frame.")
                if frame.origin == "extracted":
                    if not frame.spans:
                        raise ValueError("An explicit correction result needs a source span.")
                    validate_source_spans(description, frame.spans)
                    if any(span.origin != "extracted" for span in frame.spans):
                        raise ValueError("An explicit correction result needs extracted spans.")
        except ValueError as error:
            return ProvenanceCheck(name="explicit_provenance", passed=False, detail=str(error))
        return ProvenanceCheck(
            name="explicit_provenance",
            passed=True,
            detail="Every explicit result has an exact source span.",
        )

    @staticmethod
    def _derived_provenance_check(
        proposal: CorrectionProposal,
        input_frames: list[RequirementFrame],
        description: str,
    ) -> ProvenanceCheck:
        inputs = {frame.id: frame for frame in input_frames}
        try:
            for frame in proposal.proposed_frames:
                if not frame.origin.startswith("derived:"):
                    continue
                parent_id = frame.origin.removeprefix("derived:")
                if parent_id not in inputs:
                    raise ValueError("A derived correction must reference a local input frame.")
                if not _has_verified_ancestor(inputs[parent_id], inputs, description, set()):
                    raise ValueError(
                        "A derived correction has no continuous verified source chain."
                    )
        except ValueError as error:
            return ProvenanceCheck(name="derived_provenance", passed=False, detail=str(error))
        return ProvenanceCheck(
            name="derived_provenance",
            passed=True,
            detail="Every derived result has a continuous chain to a verified input frame.",
        )


def _has_verified_ancestor(
    frame: RequirementFrame,
    frames: dict[str, RequirementFrame],
    description: str,
    seen: set[str],
) -> bool:
    if frame.id in seen:
        return False
    if frame.origin == "extracted":
        try:
            validate_source_spans(description, frame.spans)
        except ValueError:
            return False
        return bool(frame.spans)
    if not frame.origin.startswith("derived:"):
        return False
    parent = frames.get(frame.origin.removeprefix("derived:"))
    return parent is not None and _has_verified_ancestor(
        parent, frames, description, seen | {frame.id}
    )


def _unique_spans(spans: Iterable[SourceSpan]) -> list[SourceSpan]:
    result: list[SourceSpan] = []
    seen: set[tuple[int, int, str, str]] = set()
    for span in spans:
        key = (span.start_offset, span.end_offset, span.text, span.origin)
        if key not in seen:
            seen.add(key)
            result.append(span)
    return result
