import asyncio
import os
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.infrastructure.rate_limits.redis_session_creation_limiter import (
    RedisSessionCreationLimiter,
)
from app.modules.sessions.errors import (
    SessionCreationRateLimitExceeded,
    TooManyActiveSessions,
)

_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")


@pytest.mark.integration
def test_redis_session_creation_limiter_enforces_active_and_daily_limits() -> None:
    async def scenario() -> None:
        client = Redis.from_url(_REDIS_URL, decode_responses=True)
        try:
            await client.ping()
        except Exception:
            await client.aclose()
            pytest.skip("Redis is required for integration tests")
        limiter = RedisSessionCreationLimiter(client, 60, 2, 1)
        fingerprint = str(uuid4())
        first_session_id = str(uuid4())
        second_session_id = str(uuid4())

        await limiter.acquire(first_session_id, fingerprint)
        with pytest.raises(TooManyActiveSessions):
            await limiter.acquire(second_session_id, fingerprint)
        await limiter.release(first_session_id)
        await limiter.acquire(second_session_id, fingerprint)
        with pytest.raises(SessionCreationRateLimitExceeded):
            await limiter.acquire(str(uuid4()), fingerprint)
        await limiter.release(second_session_id)
        await client.aclose()

    asyncio.run(scenario())
