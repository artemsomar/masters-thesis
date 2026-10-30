from pydantic import Field

from app.modules.diagrams.contracts.corrections import DetectedDefect, ProvenanceDecision
from app.modules.diagrams.contracts.provenance import ContractSchema
from app.modules.diagrams.schemas import Diagram


class PipelineVersions(ContractSchema):
    frame_extraction_prompt: str = Field(min_length=1, serialization_alias="frameExtractionPrompt")
    local_correction_prompts: dict[str, str] = Field(
        default_factory=dict, serialization_alias="localCorrectionPrompts"
    )
    defect_rules: str = Field(min_length=1, serialization_alias="defectRules")
    assurance_rules: str = Field(min_length=1, serialization_alias="assuranceRules")
    embedding_model: str | None = Field(default=None, serialization_alias="embeddingModel")
    similarity_threshold: float | None = Field(
        default=None, ge=0, le=1, serialization_alias="similarityThreshold"
    )


class RawDiagram(ContractSchema):
    diagram: Diagram
    pipeline_versions: PipelineVersions = Field(serialization_alias="pipelineVersions")


class FinalDiagram(ContractSchema):
    diagram: Diagram
    pipeline_versions: PipelineVersions = Field(serialization_alias="pipelineVersions")


class AutomaticDiagramFix(ContractSchema):
    rule: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2_000)
    affected_element_ids: list[str] = Field(
        default_factory=list, serialization_alias="affectedElementIds"
    )


class UnverifiedDiagramElement(ContractSchema):
    kind: str = Field(min_length=1, max_length=100)
    element_id: str = Field(min_length=1, max_length=100, serialization_alias="elementId")
    reason: str = Field(min_length=1, max_length=2_000)


class DiagramAssuranceWarning(ContractSchema):
    rule: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=2_000)
    affected_element_ids: list[str] = Field(
        default_factory=list, serialization_alias="affectedElementIds"
    )


class DiagramQualityReport(ContractSchema):
    automatic_fixes: list[AutomaticDiagramFix] = Field(
        default_factory=list, serialization_alias="automaticFixes"
    )
    remaining_defects: list[DetectedDefect] = Field(
        default_factory=list, serialization_alias="remainingDefects"
    )
    unverified_elements: list[UnverifiedDiagramElement] = Field(
        default_factory=list, serialization_alias="unverifiedElements"
    )
    provenance_decisions: list[ProvenanceDecision] = Field(
        default_factory=list, serialization_alias="provenanceDecisions"
    )
    assurance_warnings: list[DiagramAssuranceWarning] = Field(
        default_factory=list, serialization_alias="assuranceWarnings"
    )
