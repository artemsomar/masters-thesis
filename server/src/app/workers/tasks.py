import asyncio

import structlog
from redis import Redis
from rq import get_current_job
from rq.job import Job

from app.bootstrap import build_container
from app.infrastructure.llm.client import LlmProviderError
from app.modules.sessions.errors import SessionNotFound

logger = structlog.get_logger(__name__)


def process_session(session_id: str) -> None:
    job = get_current_job()
    if job is not None and isinstance(job.meta.get("correlation_id"), str):
        structlog.contextvars.bind_contextvars(correlation_id=job.meta["correlation_id"])
    container = build_container()
    try:
        asyncio.run(container.diagram_session_workflow.process_session(session_id))
    except LlmProviderError:
        logger.warning(
            "session_processing_retry_scheduled",
            session_id=session_id,
            retries_left=job.retries_left if job is not None else None,
        )
        raise
    except SessionNotFound:
        logger.info("session_processing_cancelled", session_id=session_id)
    except Exception:
        logger.exception("session_processing_failed", session_id=session_id)
        asyncio.run(_mark_session_as_failed(session_id))
    finally:
        structlog.contextvars.clear_contextvars()


def mark_session_processing_failed(
    job: Job,
    _: Redis,
    __: type[BaseException],
    ___: BaseException,
    ____: object,
) -> None:
    if job.should_retry:
        return
    session_id = str(job.args[0])
    logger.error("session_processing_retries_exhausted", session_id=session_id)
    asyncio.run(_mark_session_as_failed(session_id))


async def _mark_session_as_failed(session_id: str) -> None:
    container = build_container()
    try:
        await container.session_service.fail(session_id, "session_processing_failed")
    except SessionNotFound:
        return
