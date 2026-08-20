from app.errors import AppError


class SessionNotFound(AppError):
    def __init__(self) -> None:
        super().__init__("session_not_found", "Session was not found")


class InvalidSessionToken(AppError):
    def __init__(self) -> None:
        super().__init__("invalid_session_token", "Session token is invalid")


class InvalidSessionState(AppError):
    def __init__(self) -> None:
        super().__init__("invalid_session_state", "The requested session transition is not allowed")


class QuestionsNotAvailable(AppError):
    def __init__(self) -> None:
        super().__init__(
            "questions_not_available", "There are no questions available for this session"
        )


class InvalidQuestionRound(AppError):
    def __init__(self) -> None:
        super().__init__("invalid_question_round", "The question round is no longer current")


class SessionCreationRateLimitExceeded(AppError):
    def __init__(self) -> None:
        super().__init__(
            "session_creation_rate_limit_exceeded", "Session creation limit was reached"
        )


class TooManyActiveSessions(AppError):
    def __init__(self) -> None:
        super().__init__("too_many_active_sessions", "Too many active sessions")


class DescriptionTooLong(AppError):
    def __init__(self) -> None:
        super().__init__("description_too_long", "The system description is too long")


class AnswerTooLong(AppError):
    def __init__(self) -> None:
        super().__init__("answer_too_long", "An answer is too long")
