from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import UUID, uuid4

import structlog
from fastapi import FastAPI
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.api.exception_handlers import register_exception_handlers
from app.api.routes.diagram_sessions import router as diagram_sessions_router
from app.api.routes.health import router as health_router
from app.bootstrap import ApplicationContainer, build_container
from app.config import Settings

logger = structlog.get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    container = build_container(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("application_started", environment=container.settings.environment)
        yield
        await container.async_redis.aclose()
        container.sync_redis.close()
        logger.info("application_stopped")

    app = FastAPI(
        title="UML Diagram Backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def bind_request_context(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        correlation_id = _correlation_id(request.headers.get("X-Request-ID"))
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = correlation_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()

    app.state.container = container
    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(diagram_sessions_router)
    return app


app = create_app()


def _correlation_id(value: str | None) -> str:
    if value is not None:
        try:
            return str(UUID(value))
        except ValueError:
            pass
    return str(uuid4())
