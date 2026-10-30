import json
from datetime import datetime
from typing import Awaitable, cast

from redis.asyncio import Redis

from app.modules.projects.models import Project


class RedisProjectRepository:
    _UPDATE_SCRIPT = """
local value = redis.call('GET', KEYS[1])
if not value then return nil end
local project = cjson.decode(value)
for key, field in pairs(cjson.decode(ARGV[1])) do project[key] = field end
local updated = cjson.encode(project)
redis.call('SET', KEYS[1], updated, 'XX', 'KEEPTTL')
return updated
"""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, project_id: str) -> Project | None:
        value = await self._client.get(self._key(project_id))
        if value is None:
            return None
        return self._deserialize(value)

    async def save_new(self, project: Project, ttl_seconds: int) -> None:
        await self._client.set(self._key(project.id), self._serialize(project), ex=ttl_seconds)

    async def save_existing(self, project: Project) -> bool:
        key = self._key(project.id)
        remaining_ttl = await self._client.ttl(key)
        if remaining_ttl <= 0:
            return False
        await self._client.set(key, self._serialize(project), ex=remaining_ttl)
        return True

    async def delete(self, project_id: str) -> None:
        await self._client.delete(self._key(project_id))

    async def update(
        self,
        project_id: str,
        updated_at: datetime,
        *,
        name: str | None = None,
        document_xml: str | None = None,
    ) -> Project | None:
        fields = {"updatedAt": updated_at.isoformat()}
        if name is not None:
            fields["name"] = name
        if document_xml is not None:
            fields["documentXml"] = document_xml
        value = await cast(
            Awaitable[bytes | str | None],
            self._client.eval(self._UPDATE_SCRIPT, 1, self._key(project_id), json.dumps(fields)),
        )
        return self._deserialize(value) if value is not None else None

    @staticmethod
    def _key(project_id: str) -> str:
        return f"project:{project_id}"

    @staticmethod
    def _serialize(project: Project) -> str:
        return json.dumps(
            {
                "projectId": project.id,
                "tokenHash": project.token_hash,
                "name": project.name,
                "documentXml": project.document_xml,
                "createdAt": project.created_at.isoformat(),
                "updatedAt": project.updated_at.isoformat(),
                "expiresAt": project.expires_at.isoformat(),
            }
        )

    @staticmethod
    def _deserialize(value: bytes | str) -> Project:
        payload = json.loads(value)
        return Project(
            id=payload["projectId"],
            token_hash=payload["tokenHash"],
            name=payload["name"],
            document_xml=payload["documentXml"],
            created_at=datetime.fromisoformat(payload["createdAt"]),
            updated_at=datetime.fromisoformat(payload["updatedAt"]),
            expires_at=datetime.fromisoformat(payload["expiresAt"]),
        )
