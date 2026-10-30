from enum import StrEnum
from typing import Annotated

from pydantic import Field, model_validator

from app.modules.diagrams.contracts.provenance import ContractSchema, Origin, SourceSpan
from app.modules.diagrams.contracts.requirements import FrameIdentifier, RequirementText

GraphIdentifier = Annotated[
    str,
    Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9-]*$"),
]


class RequirementNodeType(StrEnum):
    ACTOR = "actor"
    ACTION = "action"
    OBJECT = "object"
    REQUIREMENT = "requirement"


class RequirementEdgeType(StrEnum):
    PERFORMS = "PERFORMS"
    TARGETS = "TARGETS"
    SIMILAR = "SIMILAR"


class RequirementGraphNode(ContractSchema):
    id: GraphIdentifier
    type: RequirementNodeType
    label: str = Field(min_length=1, max_length=500)
    frame_ids: list[FrameIdentifier] = Field(default_factory=list, serialization_alias="frameIds")
    spans: list[SourceSpan] = Field(default_factory=list)
    origin: Origin
    condition: RequirementText | None = None


class RequirementGraphEdge(ContractSchema):
    type: RequirementEdgeType
    source_id: GraphIdentifier = Field(serialization_alias="sourceId")
    target_id: GraphIdentifier = Field(serialization_alias="targetId")
    frame_ids: list[FrameIdentifier] = Field(default_factory=list, serialization_alias="frameIds")
    spans: list[SourceSpan] = Field(default_factory=list)
    origin: Origin


class RequirementGraph(ContractSchema):
    nodes: list[RequirementGraphNode]
    edges: list[RequirementGraphEdge]

    @model_validator(mode="after")
    def validate_references(self) -> "RequirementGraph":
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Requirement graph node identifiers must be unique")
        known_node_ids = set(node_ids)
        if any(
            edge.source_id not in known_node_ids or edge.target_id not in known_node_ids
            for edge in self.edges
        ):
            raise ValueError("Requirement graph edges must reference existing nodes")
        return self
