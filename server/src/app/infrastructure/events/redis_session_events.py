import asyncio
import json
from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.modules.sessions.enums import SessionStatus


class RedisSessionEventBroker:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def publish_status(self, session_id: str, status: SessionStatus) -> None:
        await self._client.publish(self._channel(session_id), json.dumps({"status": status}))

    async def subscribe_statuses(self, session_id: str) -> AsyncIterator[SessionStatus | None]:
        async with self._client.pubsub() as pubsub:
            await pubsub.subscribe(self._channel(session_id))
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                if message is None:
                    yield None
                    await asyncio.sleep(0)
                    continue
                payload = json.loads(message["data"])
                yield SessionStatus(payload["status"])

    def _channel(self, session_id: str) -> str:
        return f"diagram-session-events:{session_id}"
