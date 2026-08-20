from pydantic import BaseModel, ConfigDict, Field


class ClarificationSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ClarificationQuestion(ClarificationSchema):
    id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9-]*$",
        description="Stable identifier used to match this question with a user answer.",
    )
    text: str = Field(
        min_length=1,
        max_length=1_000,
        description="One essential open-ended question needed to clarify the system.",
    )
    required: bool = Field(
        default=True,
        description="Whether the user must answer this question before generation can continue.",
    )


class ClarificationResult(ClarificationSchema):
    questions: list[ClarificationQuestion] = Field(
        default_factory=list,
        description="Only essential unresolved questions. Empty when the description is sufficient.",
    )
