from dataclasses import dataclass, field
from datetime import datetime

from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.schemas import Answer, Question


@dataclass(slots=True)
class DiagramSession:
    id: str
    token_hash: str
    description: str
    language: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    current_job_id: str | None = None
    question_round: int = 0
    questions: list[Question] = field(default_factory=list)
    answers: list[Answer] = field(default_factory=list)
    analysis_facts: list[str] = field(default_factory=list)
    analysis_prompt_version: str | None = None
    diagram_json: str | None = None
    diagram_prompt_version: str | None = None
    error_code: str | None = None
