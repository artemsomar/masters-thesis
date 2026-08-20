from dataclasses import dataclass, field
from datetime import datetime

from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.schemas import ClarificationHistoryEntry, Question


@dataclass(slots=True)
class DiagramSession:
    id: str
    token_hash: str
    description: str
    language: str
    clarifications_enabled: bool
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    current_job_id: str | None = None
    question_round: int = 0
    questions: list[Question] = field(default_factory=list)
    clarification_history: list[ClarificationHistoryEntry] = field(default_factory=list)
    clarification_prompt_version: str | None = None
    diagram_json: str | None = None
    diagram_prompt_version: str | None = None
    error_code: str | None = None
