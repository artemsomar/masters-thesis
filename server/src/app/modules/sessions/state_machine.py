from app.modules.sessions.enums import SessionStatus

_ALLOWED_TRANSITIONS: dict[SessionStatus, frozenset[SessionStatus]] = {
    SessionStatus.CREATED: frozenset({SessionStatus.ANALYZING, SessionStatus.CANCELLED}),
    SessionStatus.ANALYZING: frozenset(
        {
            SessionStatus.AWAITING_ANSWERS,
            SessionStatus.GENERATING_DIAGRAM,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        }
    ),
    SessionStatus.AWAITING_ANSWERS: frozenset(
        {SessionStatus.GENERATING_DIAGRAM, SessionStatus.FAILED, SessionStatus.CANCELLED}
    ),
    SessionStatus.GENERATING_DIAGRAM: frozenset(
        {
            SessionStatus.AWAITING_ANSWERS,
            SessionStatus.DIAGRAM_READY,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        }
    ),
    SessionStatus.DIAGRAM_READY: frozenset(),
    SessionStatus.FAILED: frozenset(),
    SessionStatus.CANCELLED: frozenset(),
    SessionStatus.EXPIRED: frozenset(),
}


def is_allowed(source: SessionStatus, target: SessionStatus) -> bool:
    return target in _ALLOWED_TRANSITIONS[source]
