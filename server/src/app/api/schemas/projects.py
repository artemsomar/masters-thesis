from datetime import datetime

from pydantic import Field, field_validator

from app.api.schemas.diagram_sessions import ApiSchema


class CreateProjectRequest(ApiSchema):
    name: str = Field(default="Untitled diagram", max_length=120)


class ProjectMetadataResponse(ApiSchema):
    project_id: str = Field(serialization_alias="projectId")
    name: str
    updated_at: datetime = Field(serialization_alias="updatedAt")
    expires_at: datetime = Field(serialization_alias="expiresAt")


class CreateProjectResponse(ProjectMetadataResponse):
    project_token: str = Field(serialization_alias="projectToken")
    document_xml: str = Field(serialization_alias="documentXml")


class ProjectResponse(ProjectMetadataResponse):
    document_xml: str = Field(serialization_alias="documentXml")


class UpdateProjectRequest(ApiSchema):
    document_xml: str = Field(min_length=1, max_length=2_000_000, validation_alias="documentXml")


class RenameProjectRequest(ApiSchema):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Project name cannot be blank")
        return value.strip()


class AvailableProjectAccess(ApiSchema):
    project_id: str = Field(validation_alias="projectId")
    project_token: str = Field(validation_alias="projectToken")


class AvailableProjectsRequest(ApiSchema):
    projects: list[AvailableProjectAccess] = Field(max_length=100)
