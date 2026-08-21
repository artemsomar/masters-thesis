from typing import Annotated, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.modules.diagrams.enums import ActorType, RelationType

DiagramIdentifier = Annotated[
    str,
    Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9-]*$"),
]


class DiagramSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class DiagramGenerationRequest(DiagramSchema):
    description: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=10)
    clarification_context: str = Field(min_length=1)


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


class DiagramRelation(DiagramSchema):
    type: RelationType = Field(
        description="The UML relationship type: association, include, extend, or generalization.",
    )
    source_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("source_id", "sourceId"),
        serialization_alias="sourceId",
        description="The identifier at the source of the relationship.",
    )
    target_id: DiagramIdentifier = Field(
        validation_alias=AliasChoices("target_id", "targetId"),
        serialization_alias="targetId",
        description="The identifier at the target of the relationship.",
    )


class DiagramContent(DiagramSchema):
    system: DiagramSystem = Field(description="The boundary of the described system.")
    actors: list[Actor] = Field(
        description="External roles or systems that interact directly with the system boundary.",
    )
    use_cases: list[UseCase] = Field(
        validation_alias=AliasChoices("use_cases", "useCases"),
        serialization_alias="useCases",
        description="Goal-oriented system capabilities available to actors.",
    )
    relations: list[DiagramRelation] = Field(
        description="Semantic UML relationships that reference existing actor or use case identifiers.",
    )
    assumptions: list[str] = Field(
        description="Only material assumptions made because the available requirements were ambiguous.",
    )
    warnings: list[str] = Field(
        description="Only material limitations or unresolved ambiguities that may affect the diagram.",
    )


class DiagramGenerationOutput(DiagramContent):
    pass


class Diagram(DiagramContent):
    schema_version: Literal["1.0"] = Field(
        validation_alias=AliasChoices("schema_version", "schemaVersion"),
        serialization_alias="schemaVersion",
        description="The fixed compatibility version of this diagram JSON contract.",
    )
