import asyncio
import json

import httpx
import pytest

from app.modules.analysis.schemas import AnalysisResult
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
def test_diagram_endpoint_returns_pending_then_a_valid_diagram() -> None:
    async def scenario() -> None:
        app = create_test_app(AnalysisResult(facts=["Clients can book services"]))
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

        assert pending.status_code == 202
        assert pending.json() == {"status": "analyzing"}
        assert ready.status_code == 200
        assert ready.json()["schemaVersion"] == "1.0"
        assert ready.json()["relations"] == [
            {"type": "association", "sourceId": "client", "targetId": "book-service"}
        ]

    asyncio.run(scenario())


@pytest.mark.api
def test_session_events_stream_status_events() -> None:
    async def scenario() -> None:
        transport = httpx.ASGITransport(app=create_test_app())
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

        event = json.loads(response.text.split("data: ", maxsplit=1)[1])
        assert response.headers["content-type"].startswith("text/event-stream")
        assert event["status"] == "analyzing"
        assert event["correlationId"]

    asyncio.run(scenario())


@pytest.mark.api
def test_questions_and_answers_follow_the_current_round_contract() -> None:
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
            await app.state.container.diagram_session_workflow.process_session(session_id)

            questions = await client.get(
                f"/api/v1/diagram-sessions/{session_id}/questions", headers=headers
            )
            submitted = await client.post(
                f"/api/v1/diagram-sessions/{session_id}/answers",
                headers=headers,
                json={
                    "round": 1,
                    "answers": [
                        {
                            "questionId": "confirmation-channel",
                            "value": "By email",
                        }
                    ],
                },
            )
            repeated = await client.post(
                f"/api/v1/diagram-sessions/{session_id}/answers",
                headers=headers,
                json={"round": 1, "answers": []},
            )

        assert questions.status_code == 200
        assert questions.json() == {
            "round": 1,
            "questions": [
                {
                    "id": "confirmation-channel",
                    "text": "How is a booking confirmed?",
                    "required": True,
                }
            ],
        }
        assert submitted.status_code == 202
        assert submitted.json() == {"status": "generating_diagram"}
        assert repeated.status_code == 409

    asyncio.run(scenario())
