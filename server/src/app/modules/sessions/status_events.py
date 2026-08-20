import structlog

from app.logging_config import get_correlation_id
from app.modules.sessions.models import DiagramSession
from app.modules.sessions.ports import SessionEventPublisher
from app.modules.sessions.schemas import SessionStatusUpdate

logger = structlog.get_logger(__name__)


async def publish_status(event_publisher: SessionEventPublisher, session: DiagramSession) -> None:
    logger.info(
        "session_status_changed",
        session_id=session.id,
        status=session.status,
        error_code=session.error_code,
    )
    await event_publisher.publish_status(
        session.id,
        SessionStatusUpdate(
            status=session.status,
            error_code=session.error_code,
            correlation_id=get_correlation_id(),
        ),
    )
