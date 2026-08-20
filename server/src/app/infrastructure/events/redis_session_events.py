import asyncio
import json
from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.modules.sessions.schemas import SessionStatusUpdate


class RedisSessionEventBroker:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def publish_status(self, session_id: str, event: SessionStatusUpdate) -> None:
        await self._client.publish(
            self._channel(session_id), event.model_dump_json(by_alias=True, exclude_none=True)
        )

    async def subscribe_statuses(
        self, session_id: str
    ) -> AsyncIterator[SessionStatusUpdate | None]:
        async with self._client.pubsub() as pubsub:
            await pubsub.subscribe(self._channel(session_id))
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                if message is None:
                    yield None
                    await asyncio.sleep(0)
                    continue
                payload = json.loads(message["data"])
                yield SessionStatusUpdate.model_validate(payload)

    def _channel(self, session_id: str) -> str:
        return f"diagram-session-events:{session_id}"
