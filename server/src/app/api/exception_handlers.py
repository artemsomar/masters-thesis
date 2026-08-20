from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import AppError
from app.modules.sessions.errors import (
    InvalidQuestionRound,
    InvalidSessionState,
    InvalidSessionToken,
    QuestionsNotAvailable,
    SessionNotFound,
    SessionCreationRateLimitExceeded,
    TooManyActiveSessions,
)


def status_code_for(error: AppError) -> int:
    if isinstance(error, SessionNotFound):
        return 404
    if isinstance(error, InvalidSessionToken):
        return 401
    if isinstance(error, (InvalidSessionState, InvalidQuestionRound, QuestionsNotAvailable)):
        return 409
    if isinstance(error, (SessionCreationRateLimitExceeded, TooManyActiveSessions)):
        return 429
    return 400


async def app_error_handler(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, AppError)
    return JSONResponse(
        status_code=status_code_for(error),
        content={"error": {"code": error.code, "message": error.message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
