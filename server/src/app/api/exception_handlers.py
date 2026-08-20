from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import AppError


async def app_error_handler(_: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, AppError)
    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.code, "message": error.message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
