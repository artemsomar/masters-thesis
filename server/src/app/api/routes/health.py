import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.dependencies import get_container
from app.bootstrap import ApplicationContainer

router = APIRouter(tags=["system"])
logger = structlog.get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", response_model=None)
async def readiness(
    container: ApplicationContainer = Depends(get_container),
) -> dict[str, str] | JSONResponse:
    try:
        await container.async_redis.ping()
    except Exception:
        logger.warning("readiness_check_failed", dependency="redis")
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}
