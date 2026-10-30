from enum import StrEnum

from pydantic import Field, model_validator

from app.modules.diagrams.contracts.graph import GraphIdentifier
from app.modules.diagrams.contracts.provenance import ContractSchema, SourceSpan
from app.modules.diagrams.contracts.requirements import FrameIdentifier, RequirementFrame


class DefectType(StrEnum):
    INCOMPLETE_FRAME = "incomplete_frame"
    COMPOUND_STATEMENT = "compound_statement"
    VAGUE_VERB = "vague_verb"
    INCONSISTENT_TERMINOLOGY = "inconsistent_terminology"
    ACTION_STEP = "action_step"


class CorrectionOperation(StrEnum):
    RESOLVE = "RESOLVE"
    SPLIT = "SPLIT"
    SPECIFY = "SPECIFY"
    UNIFY = "UNIFY"
    MERGE_STEPS = "MERGE_STEPS"


class DetectedDefect(ContractSchema):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9-]*$")
    type: DefectType
    frame_ids: list[FrameIdentifier] = Field(default_factory=list, serialization_alias="frameIds")
    node_ids: list[GraphIdentifier] = Field(default_factory=list, serialization_alias="nodeIds")
    evidence: str = Field(min_length=1, max_length=2_000)
    assigned_operation: CorrectionOperation = Field(serialization_alias="assignedOperation")

    @model_validator(mode="after")
    def validate_target(self) -> "DetectedDefect":
        if not self.frame_ids and not self.node_ids:
            raise ValueError("Detected defect must reference frames or graph nodes")
        return self


class CorrectionProposal(ContractSchema):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9-]*$")
    defect_id: str = Field(min_length=1, max_length=100, serialization_alias="defectId")
    operation: CorrectionOperation
    input_frame_ids: list[FrameIdentifier] = Field(
        min_length=1, serialization_alias="inputFrameIds"
    )
    proposed_frames: list[RequirementFrame] = Field(
        min_length=1, serialization_alias="proposedFrames"
    )


class ProvenanceDecisionStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ProvenanceCheck(ContractSchema):
    name: str = Field(min_length=1, max_length=100)
    passed: bool
    detail: str = Field(min_length=1, max_length=2_000)


class ProvenanceDecision(ContractSchema):
    proposal_id: str = Field(min_length=1, max_length=100, serialization_alias="proposalId")
    defect_id: str = Field(min_length=1, max_length=100, serialization_alias="defectId")
    status: ProvenanceDecisionStatus
    reason: str = Field(min_length=1, max_length=2_000)
    checks: list[ProvenanceCheck]
    verified_spans: list[SourceSpan] = Field(
        default_factory=list, serialization_alias="verifiedSpans"
    )
