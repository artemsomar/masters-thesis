from dataclasses import dataclass, field
from datetime import datetime

from app.modules.evaluation.run_enums import EvaluationRunStatus
from app.modules.evaluation.schemas import DiagramEvaluationResult


@dataclass(slots=True)
class EvaluationRun:
    id: str
    status: EvaluationRunStatus
    limit: int | None
    created_at: datetime
    updated_at: datetime
    current_job_id: str | None = None
    results: list[DiagramEvaluationResult] = field(default_factory=list)
    error_code: str | None = None
