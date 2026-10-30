from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.modules.diagrams.schemas import Diagram
from app.modules.diagrams.contracts.results import DiagramQualityReport, PipelineVersions
from app.modules.evaluation.enums import EvaluationRelationType


class EvaluationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class EvaluationCase(EvaluationSchema):
    case_id: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("case_id", "caseId"),
        serialization_alias="caseId",
        description="Stable identifier of one dataset case.",
    )
    description: str = Field(
        min_length=1,
        description="System description supplied to the diagram generator.",
    )
    language: str = Field(
        min_length=2,
        max_length=10,
        description="Language for human-readable diagram labels.",
    )
    reference_diagram: ComparableDiagram = Field(
        description="Reference diagram normalized from the evaluation dataset.",
    )


class EvaluationNode(EvaluationSchema):
    id: str = Field(min_length=1, description="Identifier of a diagram node.")
    name: str = Field(
        min_length=1, description="Human-readable node label used for semantic matching."
    )


class EvaluationRelation(EvaluationSchema):
    type: EvaluationRelationType = Field(description="Semantic UML relation type.")
    source_id: str = Field(min_length=1, description="Identifier of the relation source node.")
    target_id: str = Field(min_length=1, description="Identifier of the relation target node.")


class ComparableDiagram(EvaluationSchema):
    actors: list[EvaluationNode] = Field(description="Actors in the diagram.")
    use_cases: list[EvaluationNode] = Field(description="Use cases in the diagram.")
    relations: list[EvaluationRelation] = Field(description="Relations in the diagram.")


class DatasetActor(EvaluationSchema):
    id: str = Field(min_length=1, description="Dataset actor identifier.")
    name: str = Field(min_length=1, description="Dataset actor label.")


class DatasetSystemBoundary(EvaluationSchema):
    label: str = Field(min_length=1, description="Dataset system boundary label.")


class DatasetSystem(EvaluationSchema):
    name: str = Field(min_length=1, description="Dataset system name.")
    boundary: DatasetSystemBoundary = Field(description="Dataset system boundary.")


class DatasetUseCase(EvaluationSchema):
    id: str = Field(min_length=1, description="Dataset use case identifier.")
    name: str = Field(min_length=1, description="Dataset use case label.")


class DatasetRelation(EvaluationSchema):
    type: EvaluationRelationType = Field(description="Dataset UML relation type.")
    source: str = Field(min_length=1, description="Dataset relation source identifier.")
    target: str = Field(min_length=1, description="Dataset relation target identifier.")


class DatasetDiagram(EvaluationSchema):
    system: DatasetSystem = Field(description="System supplied by the dataset.")
    actors: list[DatasetActor] = Field(description="Actors supplied by the dataset.")
    use_cases: list[DatasetUseCase] = Field(description="Use cases supplied by the dataset.")
    relationships: list[DatasetRelation] = Field(description="Relations supplied by the dataset.")


class F1Score(EvaluationSchema):
    precision: float = Field(ge=0, le=1, description="Precision of a matched entity set.")
    recall: float = Field(ge=0, le=1, description="Recall of a matched entity set.")
    f1: float = Field(ge=0, le=1, description="Harmonic mean of precision and recall.")


class RelationshipScores(EvaluationSchema):
    overall: F1Score = Field(description="Score across every relation type.")
    association: F1Score = Field(description="Score for actor-to-use-case associations.")
    include: F1Score = Field(description="Score for include relations.")
    extend: F1Score = Field(description="Score for extend relations.")
    generalization: F1Score = Field(description="Score for generalization relations.")


class DiagramEvaluationResult(EvaluationSchema):
    case_id: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("case_id", "caseId"),
        serialization_alias="caseId",
        description="Identifier of the evaluated dataset case.",
    )
    generated_diagram: Diagram | None = Field(
        validation_alias=AliasChoices("generated_diagram", "generatedDiagram"),
        serialization_alias="generatedDiagram",
        description="Generated diagram, absent when it is not UML-valid.",
    )
    initial_diagram: Diagram | None = Field(
        default=None,
        validation_alias=AliasChoices("initial_diagram", "initialDiagram"),
        serialization_alias="initialDiagram",
        description="Diagram assembled directly from the LLM's frame extraction output, "
        "before defect correction and assurance.",
    )
    final_diagram: Diagram | None = Field(
        default=None,
        validation_alias=AliasChoices("final_diagram", "finalDiagram"),
        serialization_alias="finalDiagram",
        description="Diagram after deterministic UML assurance.",
    )
    quality_report: DiagramQualityReport | None = Field(
        default=None,
        validation_alias=AliasChoices("quality_report", "qualityReport"),
        serialization_alias="qualityReport",
        description="Pipeline diagnostics and automatic assurance fixes.",
    )
    pipeline_versions: PipelineVersions | None = Field(
        default=None,
        validation_alias=AliasChoices("pipeline_versions", "pipelineVersions"),
        serialization_alias="pipelineVersions",
        description="Versions of prompts, rules, embeddings, and thresholds used in the run.",
    )
    diagram_prompt_version: str | None = Field(
        validation_alias=AliasChoices("diagram_prompt_version", "diagramPromptVersion"),
        serialization_alias="diagramPromptVersion",
        description="Version of the prompt used for generation.",
    )
    uml_validity_score: float = Field(
        ge=0,
        le=1,
        validation_alias=AliasChoices("uml_validity_score", "umlValidityScore"),
        serialization_alias="umlValidityScore",
        description="One for a schema- and UML-valid generated diagram, otherwise zero.",
    )
    actor_score: F1Score | None = Field(
        default=None,
        validation_alias=AliasChoices("actor_score", "actorScore"),
        serialization_alias="actorScore",
        description="Semantic matching score for actors.",
    )
    use_case_score: F1Score | None = Field(
        default=None,
        validation_alias=AliasChoices("use_case_score", "useCaseScore"),
        serialization_alias="useCaseScore",
        description="Semantic matching score for use cases.",
    )
    relationship_scores: RelationshipScores | None = Field(
        default=None,
        validation_alias=AliasChoices("relationship_scores", "relationshipScores"),
        serialization_alias="relationshipScores",
        description="Strict relation scores after semantic node matching.",
    )
    initial_actor_score: F1Score | None = Field(
        default=None,
        validation_alias=AliasChoices("initial_actor_score", "initialActorScore"),
        serialization_alias="initialActorScore",
        description="Semantic matching score for actors in the initial diagram.",
    )
    initial_use_case_score: F1Score | None = Field(
        default=None,
        validation_alias=AliasChoices("initial_use_case_score", "initialUseCaseScore"),
        serialization_alias="initialUseCaseScore",
        description="Semantic matching score for use cases in the initial diagram.",
    )
    initial_relationship_scores: RelationshipScores | None = Field(
        default=None,
        validation_alias=AliasChoices("initial_relationship_scores", "initialRelationshipScores"),
        serialization_alias="initialRelationshipScores",
        description="Strict relation scores for the initial diagram after semantic node matching.",
    )
