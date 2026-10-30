from pydantic import BaseModel, ConfigDict, Field

from app.modules.diagrams.enums import RelationType


class ParallelPipelineSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ActorCandidate(ParallelPipelineSchema):
    name: str = Field(min_length=1, max_length=200, description="Short canonical actor role name.")


class ActorsOutput(ParallelPipelineSchema):
    actors: list[ActorCandidate] = Field(
        description="Distinct actor roles that interact with the system."
    )


class UseCaseCandidate(ParallelPipelineSchema):
    name: str = Field(min_length=1, max_length=200, description="Short canonical use case name.")


class UseCasesOutput(ParallelPipelineSchema):
    use_cases: list[UseCaseCandidate] = Field(
        description="Distinct goal-oriented system capabilities."
    )


class RelatedPair(ParallelPipelineSchema):
    element_a: str = Field(description="Exact name of one actor or use case in the connection.")
    element_b: str = Field(description="Exact name of the other actor or use case in the connection.")


class RelatedPairsOutput(ParallelPipelineSchema):
    pairs: list[RelatedPair] = Field(
        description="Unordered pairs of elements that have a direct relationship."
    )


class TypedRelation(ParallelPipelineSchema):
    source: str = Field(description="Exact name of the element at the source of the relationship.")
    target: str = Field(description="Exact name of the element at the target of the relationship.")
    type: RelationType = Field(description="association, include, extend, or generalization.")


class TypedRelationsOutput(ParallelPipelineSchema):
    relations: list[TypedRelation] = Field(
        description="Every given pair, correctly directed and typed."
    )
