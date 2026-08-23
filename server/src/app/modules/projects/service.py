import hmac
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.projects.errors import InvalidProjectToken, ProjectNotFound
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository
from app.modules.sessions.tokens import create_token, hash_token

EMPTY_DOCUMENT_XML = '<diagram-document version="1.0"><nodes/><relations/></diagram-document>'


class ProjectService:
    def __init__(self, repository: ProjectRepository, token_pepper: str, ttl_seconds: int) -> None:
        self._repository = repository
        self._token_pepper = token_pepper
        self._ttl = timedelta(seconds=ttl_seconds)
        self._ttl_seconds = ttl_seconds

    async def create(self, name: str) -> tuple[Project, str]:
        token = create_token()
        now = datetime.now(UTC)
        project = Project(
            id=str(uuid4()),
            token_hash=hash_token(token, self._token_pepper),
            name=name.strip() or "Untitled diagram",
            document_xml=EMPTY_DOCUMENT_XML,
            created_at=now,
            updated_at=now,
            expires_at=now + self._ttl,
        )
        await self._repository.save_new(project, self._ttl_seconds)
        return project, token

    async def get_authorized(self, project_id: str, token: str) -> Project:
        project = await self.get(project_id)
        if not hmac.compare_digest(project.token_hash, hash_token(token, self._token_pepper)):
            raise InvalidProjectToken()
        return project

    async def update_document(self, project_id: str, document_xml: str) -> Project:
        project = await self.get(project_id)
        project.document_xml = document_xml
        project.updated_at = datetime.now(UTC)
        if not await self._repository.save_existing(project):
            raise ProjectNotFound()
        return project

    async def get(self, project_id: str) -> Project:
        project = await self._repository.get(project_id)
        if project is None:
            raise ProjectNotFound()
        return project

    async def delete(self, project_id: str) -> None:
        await self.get(project_id)
        await self._repository.delete(project_id)
