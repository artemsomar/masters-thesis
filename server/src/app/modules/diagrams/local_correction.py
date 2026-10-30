from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.llm.client import InvalidStructuredOutputError, StructuredLlmClient
from app.modules.diagrams.contracts.corrections import (
    CorrectionProposal,
    DetectedDefect,
    ProvenanceCheck,
    ProvenanceDecision,
    ProvenanceDecisionStatus,
)
from app.modules.diagrams.contracts.graph import RequirementGraph
from app.modules.diagrams.contracts.requirements import RequirementFrame
from app.modules.diagrams.errors import InvalidLocalCorrection
from app.modules.diagrams.local_correction_prompts import (
    PROMPT_VERSION,
    SYSTEM_INSTRUCTION,
    build_local_correction_prompt,
)
from app.modules.diagrams.provenance_gate import ProvenanceGate, ProvenanceGateResult


@dataclass(frozen=True, slots=True)
class LocalCorrectionResult:
    frames: list[RequirementFrame]
    gate_result: ProvenanceGateResult
    prompt_version: str = PROMPT_VERSION


class LocalCorrectionService:
    """Proposes one correction and lets the deterministic gate decide its fate."""

    def __init__(
        self, llm_client: StructuredLlmClient, provenance_gate: ProvenanceGate | None = None
    ) -> None:
        self._llm_client = llm_client
        self._provenance_gate = provenance_gate or ProvenanceGate()

    async def correct(
        self,
        defect: DetectedDefect,
        frames: list[RequirementFrame],
        graph: RequirementGraph,
        description: str,
    ) -> LocalCorrectionResult:
        local_frames = [frame for frame in frames if frame.id in set(defect.frame_ids)]
        if len(local_frames) != len(defect.frame_ids):
            raise InvalidLocalCorrection("missing_local_frames")
        prompt = build_local_correction_prompt(defect, local_frames, graph)
        for attempt in range(2):
            try:
                proposal = await self._llm_client.generate(
                    prompt,
                    CorrectionProposal,
                    SYSTEM_INSTRUCTION,
                )
            except InvalidStructuredOutputError:
                if attempt == 0:
                    prompt += (
                        "\nThe previous response failed schema validation. Return a valid "
                        "CorrectionProposal. Copy supporting spans and their absolute offsets "
                        "from the input frames; never invent placeholder offsets."
                    )
                    continue
                reason = "Correction rejected after two responses failed schema validation."
                gate_result = ProvenanceGateResult(
                    accepted=False,
                    frames=local_frames,
                    decision=ProvenanceDecision(
                        proposal_id=f"invalid-{defect.id}"[:100],
                        defect_id=defect.id,
                        status=ProvenanceDecisionStatus.REJECTED,
                        reason=reason,
                        checks=[
                            ProvenanceCheck(name="structured_output", passed=False, detail=reason)
                        ],
                    ),
                )
                return LocalCorrectionResult(frames=local_frames, gate_result=gate_result)
            gate_result = self._provenance_gate.evaluate(
                proposal, defect, local_frames, description
            )
            return LocalCorrectionResult(frames=gate_result.frames, gate_result=gate_result)
        raise AssertionError("Unreachable correction attempt state")
