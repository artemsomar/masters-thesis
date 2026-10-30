import asyncio
import json

import httpx
import pytest

from tests.api.diagram_sessions_app import create_test_app


@pytest.mark.api
def test_session_endpoints_require_a_token_and_delete_the_session() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=create_test_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/diagram-sessions",
                json={"description": "A booking system", "language": "en"},
            )
            payload = created.json()
            headers = {"Authorization": f"Bearer {payload['sessionToken']}"}
            unauthorized = await client.get(f"/api/v1/diagram-sessions/{payload['sessionId']}")
            deleted = await client.delete(
                f"/api/v1/diagram-sessions/{payload['sessionId']}", headers=headers
            )

        assert created.status_code == 202
        assert payload["status"] == "analyzing"
        assert unauthorized.status_code == 401
        assert deleted.status_code == 204

    asyncio.run(scenario())


@pytest.mark.api
def test_diagram_endpoint_returns_only_final_after_pipeline_completion() -> None:
    async def scenario() -> None:
        app = create_test_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/diagram-sessions",
                json={"description": "A booking system", "language": "en"},
            )
            payload = created.json()
            session_id = payload["sessionId"]
            headers = {"Authorization": f"Bearer {payload['sessionToken']}"}
            pending = await client.get(
                f"/api/v1/diagram-sessions/{session_id}/diagram", headers=headers
            )
            await app.state.container.diagram_session_workflow.process_session(session_id)
            ready = await client.get(
                f"/api/v1/diagram-sessions/{session_id}/diagram", headers=headers
            )
            stored = await app.state.container.session_service.get(session_id)

        assert pending.status_code == 202
        assert ready.status_code == 200
        assert ready.json()["relations"][0]["origin"] == "unverified"
        assert "rawDiagram" not in ready.json()
        assert stored.raw_diagram_json is not None
        assert stored.final_diagram_json is not None
        assert stored.quality_report_json is not None

    asyncio.run(scenario())


@pytest.mark.api
def test_session_events_include_pipeline_phase() -> None:
    async def scenario() -> None:
        app = create_test_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/diagram-sessions",
                json={"description": "A booking system", "language": "en"},
            )
            payload = created.json()
            await app.state.container.diagram_session_workflow.process_session(payload["sessionId"])
            response = await client.get(
                f"/api/v1/diagram-sessions/{payload['sessionId']}/events",
                headers={"Authorization": f"Bearer {payload['sessionToken']}"},
            )

        events = [
            json.loads(line.removeprefix("data: "))
            for line in response.text.splitlines()
            if line.startswith("data: ")
        ]
        assert response.headers["content-type"].startswith("text/event-stream")
        assert any(event.get("phase") == "extracting_frames" for event in events)
        assert events[-1]["status"] == "diagram_ready"

    asyncio.run(scenario())


@pytest.mark.api
def test_session_api_does_not_expose_clarifications() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=create_test_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/diagram-sessions",
                json={"description": "A booking system", "language": "en"},
            )
            payload = created.json()
            headers = {"Authorization": f"Bearer {payload['sessionToken']}"}
            questions = await client.get(
                f"/api/v1/diagram-sessions/{payload['sessionId']}/questions", headers=headers
            )
            flagged = await client.post(
                "/api/v1/diagram-sessions",
                json={
                    "description": "A booking system",
                    "language": "en",
                    "clarificationsEnabled": False,
                },
            )

        assert questions.status_code == 404
        assert flagged.status_code == 422

    asyncio.run(scenario())
