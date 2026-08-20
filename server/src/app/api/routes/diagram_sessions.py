from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_authorized_session, get_container
from app.api.schemas.diagram_sessions import (
    CreateDiagramSessionRequest,
    CreateDiagramSessionResponse,
    NextAction,
    SessionStatusEvent,
    SessionStatusResponse,
)
from app.bootstrap import ApplicationContainer
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession

router = APIRouter(prefix="/api/v1/diagram-sessions", tags=["diagram-sessions"])


@router.post("", response_model=CreateDiagramSessionResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_session(
    request: CreateDiagramSessionRequest,
    container: ApplicationContainer = Depends(get_container),
) -> CreateDiagramSessionResponse:
    session, token = await container.diagram_session_workflow.create_session(
        request.description, request.language
    )
    return CreateDiagramSessionResponse(
        session_id=session.id,
        session_token=token,
        status=session.status,
        expires_at=session.expires_at,
    )


@router.get("/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(
    session: DiagramSession = Depends(get_authorized_session),
) -> SessionStatusResponse:
    return SessionStatusResponse(
        session_id=session.id,
        status=session.status,
        next_action=_next_action(session.status),
        updated_at=session.updated_at,
    )


@router.get("/{session_id}/events")
async def stream_session_events(
    request: Request,
    session: DiagramSession = Depends(get_authorized_session),
    container: ApplicationContainer = Depends(get_container),
) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(request, container, session.id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session: DiagramSession = Depends(get_authorized_session),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.diagram_session_workflow.delete_session(session.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _event_stream(
    request: Request, container: ApplicationContainer, session_id: str
) -> AsyncIterator[bytes]:
    async for event in container.session_event_broker.subscribe_statuses(session_id):
        if await request.is_disconnected():
            return
        if event is None:
            yield b": keepalive\n\n"
        else:
            payload = SessionStatusEvent(status=event).model_dump_json(by_alias=True)
            yield f"event: status\ndata: {payload}\n\n".encode()


def _next_action(status_value: SessionStatus) -> NextAction:
    if status_value is SessionStatus.AWAITING_ANSWERS:
        return NextAction.GET_QUESTIONS
    if status_value is SessionStatus.DIAGRAM_READY:
        return NextAction.GET_DIAGRAM
    if status_value in {SessionStatus.FAILED, SessionStatus.CANCELLED, SessionStatus.EXPIRED}:
        return NextAction.CREATE_NEW_SESSION
    return NextAction.WAIT
