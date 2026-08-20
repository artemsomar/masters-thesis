from enum import StrEnum


class SessionStatus(StrEnum):
    CREATED = "created"
    ANALYZING = "analyzing"
    AWAITING_ANSWERS = "awaiting_answers"
    GENERATING_DIAGRAM = "generating_diagram"
    DIAGRAM_READY = "diagram_ready"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
