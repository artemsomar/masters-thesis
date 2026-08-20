import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import uuid4

import pytest
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.client import PubSub

from app.infrastructure.repositories.redis_session_repository import RedisSessionRepository
from app.infrastructure.events.redis_session_events import RedisSessionEventBroker
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.models import DiagramSession
from app.modules.sessions.schemas import SessionStatusUpdate

_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")


def _require_redis() -> None:
    try:
        Redis.from_url(_REDIS_URL).ping()
    except Exception:
        pytest.skip("Redis is required for integration tests")


@pytest.mark.integration
def test_redis_session_repository_persists_and_deletes_a_session() -> None:
    async def scenario() -> None:
        client = AsyncRedis.from_url(_REDIS_URL, decode_responses=True)
        repository = RedisSessionRepository(client, 86_400)
        now = datetime.now(UTC)
        session = DiagramSession(
            id=str(uuid4()),
            token_hash="token-hash",
            description="A booking system",
            language="en",
            status=SessionStatus.ANALYZING,
            created_at=now,
            updated_at=now,
            expires_at=now + timedelta(hours=24),
        )
        try:
            await repository.save(session)
            restored = await repository.get(session.id)
            ttl = await client.ttl(f"diagram-session:{session.id}")
            await repository.delete(session.id)

            assert restored == session
            assert ttl > 0
            assert await repository.get(session.id) is None
        finally:
            await client.aclose()

    _require_redis()
    asyncio.run(scenario())


@pytest.mark.integration
def test_redis_event_broker_publishes_status_events() -> None:
    async def scenario() -> None:
        client = AsyncRedis.from_url(_REDIS_URL, decode_responses=True)
        broker = RedisSessionEventBroker(client)
        session_id = str(uuid4())
        try:
            async with client.pubsub() as subscription:
                await subscription.subscribe(f"diagram-session-events:{session_id}")
                await broker.publish_status(
                    session_id, SessionStatusUpdate(status=SessionStatus.ANALYZING)
                )
                message = await _next_message(subscription)

            assert message is not None
            assert json.loads(message["data"]) == {"status": "analyzing"}
        finally:
            await client.aclose()

    _require_redis()
    asyncio.run(scenario())


async def _next_message(subscription: PubSub) -> dict[str, Any] | None:
    for _ in range(2):
        message = await asyncio.wait_for(
            subscription.get_message(ignore_subscribe_messages=True, timeout=1.0), timeout=2.0
        )
        if message is not None:
            return cast(dict[str, Any], message)
    return None
