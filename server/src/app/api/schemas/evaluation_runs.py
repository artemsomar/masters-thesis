from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.modules.evaluation.run_enums import EvaluationRunStatus
from app.modules.evaluation.schemas import DiagramEvaluationResult


class EvaluationRunSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class CreateEvaluationRunRequest(EvaluationRunSchema):
    limit: int | None = Field(
        default=None,
        ge=1,
        description="Maximum number of dataset cases to evaluate; evaluates all cases when omitted.",
    )


class CreateEvaluationRunResponse(EvaluationRunSchema):
    run_id: str = Field(
        validation_alias=AliasChoices("run_id", "runId"),
        serialization_alias="runId",
    )
    status: EvaluationRunStatus


class EvaluationRunStatusResponse(EvaluationRunSchema):
    run_id: str = Field(
        validation_alias=AliasChoices("run_id", "runId"),
        serialization_alias="runId",
    )
    status: EvaluationRunStatus
    updated_at: datetime = Field(
        validation_alias=AliasChoices("updated_at", "updatedAt"),
        serialization_alias="updatedAt",
    )
    error_code: str | None = Field(
        default=None,
        validation_alias=AliasChoices("error_code", "errorCode"),
        serialization_alias="errorCode",
    )
    results: list[DiagramEvaluationResult] | None = Field(
        default=None,
        description="Per-case evaluation metrics, present once the run has completed.",
    )
