import json
from datetime import datetime

from redis.asyncio import Redis

from app.modules.projects.models import Project


class RedisProjectRepository:
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
