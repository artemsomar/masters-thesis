import asyncio

import httpx
import pytest

from app.main import create_app


@pytest.mark.api
def test_health_returns_ok() -> None:
    async def make_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app())
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/health")

    response = asyncio.run(make_request())

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
