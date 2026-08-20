import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI

from app.main import create_app
from app.modules.sessions.service import SessionService
from app.workflows.diagram_session_workflow import DiagramSessionWorkflow
from tests.fakes.fake_sessions import (
    FakeSessionEventBroker,
    FakeSessionJobDispatcher,
    FakeSessionRepository,
)


def _app() -> FastAPI:
    repository = FakeSessionRepository()
    event_broker = FakeSessionEventBroker()
    service = SessionService(repository, event_broker, "test-pepper", 86_400)
    workflow = DiagramSessionWorkflow(service, FakeSessionJobDispatcher())
    app = create_app()
    app.state.container = SimpleNamespace(
        session_service=service,
        session_event_broker=event_broker,
        diagram_session_workflow=workflow,
    )
    return app


@pytest.mark.api
def test_session_endpoints_require_a_token_and_delete_the_session() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/diagram-sessions",
                json={"description": "A booking system", "language": "en"},
            )
            payload = created.json()
            session_id = payload["sessionId"]
            headers = {"Authorization": f"Bearer {payload['sessionToken']}"}

            unauthorized = await client.get(f"/api/v1/diagram-sessions/{session_id}")
            status = await client.get(f"/api/v1/diagram-sessions/{session_id}", headers=headers)
            deleted = await client.delete(f"/api/v1/diagram-sessions/{session_id}", headers=headers)
            missing = await client.get(f"/api/v1/diagram-sessions/{session_id}", headers=headers)

        assert created.status_code == 202
        assert payload["status"] == "analyzing"
        assert unauthorized.status_code == 401
        assert status.json()["nextAction"] == "wait"
        assert deleted.status_code == 204
        assert missing.status_code == 404

    asyncio.run(scenario())


@pytest.mark.api
def test_session_events_stream_status_events() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/diagram-sessions",
                json={"description": "A booking system", "language": "en"},
            )
            payload = created.json()
            response = await client.get(
                f"/api/v1/diagram-sessions/{payload['sessionId']}/events",
                headers={"Authorization": f"Bearer {payload['sessionToken']}"},
            )

        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.text == 'event: status\ndata: {"status":"analyzing"}\n\n'

    asyncio.run(scenario())
