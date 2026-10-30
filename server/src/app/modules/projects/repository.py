from typing import Protocol
from datetime import datetime

from app.modules.projects.models import Project


class ProjectRepository(Protocol):
    async def get(self, project_id: str) -> Project | None: ...

    async def save_new(self, project: Project, ttl_seconds: int) -> None: ...

    async def save_existing(self, project: Project) -> bool: ...

    async def update(
        self,
        project_id: str,
        updated_at: datetime,
        *,
        name: str | None = None,
        document_xml: str | None = None,
    ) -> Project | None: ...

    async def delete(self, project_id: str) -> None: ...
