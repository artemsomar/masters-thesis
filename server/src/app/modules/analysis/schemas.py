from pydantic import BaseModel, ConfigDict, Field


class AnalysisSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalysisQuestion(AnalysisSchema):
    id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9-]*$",
        description="A stable kebab-case identifier that is unique within this question round.",
    )
    text: str = Field(
        min_length=1,
        max_length=1_000,
        description="One concise open-ended clarification question written in the requested language.",
    )
    required: bool = Field(
        default=True,
        description="Whether the user must answer this question before diagram generation can continue.",
    )


class AnalysisAnswer(AnalysisSchema):
    question_id: str = Field(min_length=1, max_length=100)
    value: str = Field(min_length=1)


class AnalysisResult(AnalysisSchema):
    facts: list[str] = Field(
        default_factory=list,
        max_length=100,
        description="Confirmed, diagram-relevant facts from the description and prior answers. Do not add speculation.",
    )
    questions: list[AnalysisQuestion] = Field(
        default_factory=list,
        description="Only essential unresolved questions. Return an empty list when the available information is sufficient.",
    )
