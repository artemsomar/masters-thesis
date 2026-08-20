from dataclasses import dataclass
from datetime import datetime

from app.modules.sessions.enums import SessionStatus


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
