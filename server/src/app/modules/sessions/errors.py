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
