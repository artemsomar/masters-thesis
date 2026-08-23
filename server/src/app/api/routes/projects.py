from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_authorized_project, get_container
from app.api.schemas.projects import (
    CreateProjectRequest,
    CreateProjectResponse,
    ProjectMetadataResponse,
    ProjectResponse,
    UpdateProjectRequest,
)
from app.bootstrap import ApplicationContainer
from app.modules.projects.models import Project

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", response_model=CreateProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    container: ApplicationContainer = Depends(get_container),
) -> CreateProjectResponse:
    project, token = await container.project_service.create(request.name)
    return CreateProjectResponse(
        project_id=project.id,
        project_token=token,
        name=project.name,
        document_xml=project.document_xml,
        updated_at=project.updated_at,
        expires_at=project.expires_at,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project: Project = Depends(get_authorized_project)) -> ProjectResponse:
    return ProjectResponse(
        project_id=project.id,
        name=project.name,
        document_xml=project.document_xml,
        updated_at=project.updated_at,
        expires_at=project.expires_at,
    )


@router.put("/{project_id}", response_model=ProjectMetadataResponse)
async def update_project(
    request: UpdateProjectRequest,
    project: Project = Depends(get_authorized_project),
    container: ApplicationContainer = Depends(get_container),
) -> ProjectMetadataResponse:
    updated_project = await container.project_service.update_document(
        project.id, request.document_xml
    )
    return ProjectMetadataResponse(
        project_id=updated_project.id,
        name=updated_project.name,
        updated_at=updated_project.updated_at,
        expires_at=updated_project.expires_at,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Project = Depends(get_authorized_project),
    container: ApplicationContainer = Depends(get_container),
) -> None:
    await container.project_service.delete(project.id)
