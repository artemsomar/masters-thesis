from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Project:
    id: str
    token_hash: str
    name: str
    document_xml: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ProjectAccessCredentials:
    project_id: str
    project_token: str


@dataclass(frozen=True, slots=True)
class CreatedProject:
    project: Project
    project_token: str
