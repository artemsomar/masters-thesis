from typing import cast

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.bootstrap import ApplicationContainer
from app.modules.sessions.errors import InvalidSessionToken
from app.modules.sessions.models import DiagramSession

_bearer = HTTPBearer(auto_error=False)


def get_container(request: Request) -> ApplicationContainer:
    return cast(ApplicationContainer, request.app.state.container)


async def get_authorized_session(
    session_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    container: ApplicationContainer = Depends(get_container),
) -> DiagramSession:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidSessionToken()
    return await container.session_service.get_authorized(session_id, credentials.credentials)
