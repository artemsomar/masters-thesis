from typing import Annotated, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.modules.diagrams.enums import ActorType, RelationType

DiagramIdentifier = Annotated[
    str,
    Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9-]*$"),
]


class DiagramSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DiagramGenerationAnswer(DiagramSchema):
    question_id: str = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("question_id", "questionId"),
        serialization_alias="questionId",
    )
    value: str = Field(min_length=1)


class DiagramGenerationRequest(DiagramSchema):
    description: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=10)
    facts: list[str] = Field(max_length=100)
    answers: list[DiagramGenerationAnswer]


class DiagramSystem(DiagramSchema):
    id: DiagramIdentifier = Field(
        description="A stable kebab-case identifier for the system boundary.",
    )
    name: str = Field(
        min_length=1,
        max_length=200,
        description="The concise human-readable system name in the requested language.",
    )


class Actor(DiagramSchema):
    id: DiagramIdentifier = Field(
        description="A stable kebab-case identifier that is unique across actors and use cases.",
    )
    name: str = Field(
        min_length=1,
        max_length=200,
        description="The concise human-readable actor name in the requested language.",
    )
    type: ActorType = Field(
        description="primary for an actor pursuing a main system goal; secondary for a supporting external actor.",
    )


class UseCase(DiagramSchema):
    id: DiagramIdentifier = Field(
        description="A stable kebab-case identifier that is unique across actors and use cases.",
    )
    name: str = Field(
        min_length=1,
        max_length=200,
        description="A concise goal-oriented use case name in the requested language.",
    )


class AssociationRelation(DiagramSchema):
    type: Literal[RelationType.ASSOCIATION] = Field(
        description="A direct interaction between an actor and a use case.",
    )
    source_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("source_id", "sourceId"),
        serialization_alias="sourceId",
        description="The identifier of the actor that interacts with the use case.",
    )
    target_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("target_id", "targetId"),
        serialization_alias="targetId",
        description="The identifier of the use case the actor interacts with.",
    )


class IncludeRelation(DiagramSchema):
    type: Literal[RelationType.INCLUDE] = Field(
        description="A mandatory reusable behavior included by another use case.",
    )
    source_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("source_id", "sourceId"),
        serialization_alias="sourceId",
        description="The identifier of the base use case that includes common behavior.",
    )
    target_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("target_id", "targetId"),
        serialization_alias="targetId",
        description="The identifier of the mandatory reusable use case included by sourceId.",
    )


class ExtendRelation(DiagramSchema):
    type: Literal[RelationType.EXTEND] = Field(
        description="An optional or conditional behavior that extends a base use case.",
    )
    source_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("source_id", "sourceId"),
        serialization_alias="sourceId",
        description="The identifier of the extending use case.",
    )
    target_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("target_id", "targetId"),
        serialization_alias="targetId",
        description="The identifier of the base use case extended by sourceId.",
    )


class GeneralizationRelation(DiagramSchema):
    type: Literal[RelationType.GENERALIZATION] = Field(
        description="A specialization relationship between two actors or between two use cases.",
    )
    source_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("source_id", "sourceId"),
        serialization_alias="sourceId",
        description="The identifier of the specialized actor or use case.",
    )
    target_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("target_id", "targetId"),
        serialization_alias="targetId",
        description="The identifier of the more general actor or use case.",
    )


DiagramRelation = Annotated[
    AssociationRelation | IncludeRelation | ExtendRelation | GeneralizationRelation,
    Field(discriminator="type"),
]


class Diagram(DiagramSchema):
    schema_version: Literal["1.0"] = Field(
        validation_alias=AliasChoices("schema_version", "schemaVersion"),
        serialization_alias="schemaVersion",
        description="The fixed compatibility version of this diagram JSON contract.",
    )
    system: DiagramSystem = Field(description="The boundary of the described system.")
    actors: list[Actor] = Field(
        min_length=1,
        max_length=100,
        description="External roles or systems that interact directly with the system boundary.",
    )
    use_cases: list[UseCase] = Field(
        min_length=1,
        max_length=100,
        validation_alias=AliasChoices("use_cases", "useCases"),
        serialization_alias="useCases",
        description="Goal-oriented system capabilities available to actors.",
    )
    relations: list[DiagramRelation] = Field(
        max_length=300,
        description="Semantic UML relationships that reference existing actor or use case identifiers.",
    )
    assumptions: list[str] = Field(
        max_length=100,
        description="Only material assumptions made because the available requirements were ambiguous.",
    )
    warnings: list[str] = Field(
        max_length=100,
        description="Only material limitations or unresolved ambiguities that may affect the diagram.",
    )
