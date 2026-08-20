from datetime import UTC, datetime, timedelta
from typing import Awaitable, cast

from redis.asyncio import Redis

from app.modules.sessions.errors import (
    SessionCreationRateLimitExceeded,
    TooManyActiveSessions,
)


class RedisSessionCreationLimiter:
    _ACQUIRE_SCRIPT = """
local daily_count = tonumber(redis.call('GET', KEYS[1]) or '0')
if daily_count >= tonumber(ARGV[1]) then
    return 1
end
redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', ARGV[2])
if tonumber(redis.call('ZCARD', KEYS[2])) >= tonumber(ARGV[3]) then
    return 2
end
redis.call('INCR', KEYS[1])
if daily_count == 0 then
    redis.call('EXPIRE', KEYS[1], ARGV[4])
end
redis.call('ZADD', KEYS[2], ARGV[5], ARGV[6])
redis.call('EXPIRE', KEYS[2], ARGV[7])
redis.call('SET', KEYS[3], ARGV[8], 'EX', ARGV[7])
return 0
"""
    _RELEASE_SCRIPT = """
local fingerprint = redis.call('GET', KEYS[1])
if fingerprint then
    redis.call('ZREM', 'diagram-session-rate-limit:active:' .. fingerprint, ARGV[1])
end
redis.call('DEL', KEYS[1])
"""

    def __init__(
        self,
        client: Redis,
        session_ttl_seconds: int,
        creation_limit_per_day: int,
        max_active_sessions: int,
    ) -> None:
        self._client = client
        self._session_ttl_seconds = session_ttl_seconds
        self._creation_limit_per_day = creation_limit_per_day
        self._max_active_sessions = max_active_sessions

    async def acquire(self, session_id: str, client_fingerprint: str) -> None:
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=self._session_ttl_seconds)
        result = await cast(
            Awaitable[object],
            self._client.eval(
                self._ACQUIRE_SCRIPT,
                3,
                self._daily_key(client_fingerprint, now),
                self._active_key(client_fingerprint),
                self._session_key(session_id),
                str(self._creation_limit_per_day),
                str(int(now.timestamp())),
                str(self._max_active_sessions),
                str(self._seconds_until_next_day(now)),
                str(int(expires_at.timestamp())),
                session_id,
                client_fingerprint,
                str(self._session_ttl_seconds),
            ),
        )
        if result == 1:
            raise SessionCreationRateLimitExceeded()
        if result == 2:
            raise TooManyActiveSessions()

    async def release(self, session_id: str) -> None:
        await cast(
            Awaitable[object],
            self._client.eval(self._RELEASE_SCRIPT, 1, self._session_key(session_id), session_id),
        )

    def _daily_key(self, client_fingerprint: str, now: datetime) -> str:
        return f"diagram-session-rate-limit:daily:{now:%Y-%m-%d}:{client_fingerprint}"

    def _active_key(self, client_fingerprint: str) -> str:
        return f"diagram-session-rate-limit:active:{client_fingerprint}"

    def _session_key(self, session_id: str) -> str:
        return f"diagram-session-rate-limit:session:{session_id}"

    def _seconds_until_next_day(self, now: datetime) -> int:
        next_day = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), UTC)
        return max(1, int((next_day - now).total_seconds()))
