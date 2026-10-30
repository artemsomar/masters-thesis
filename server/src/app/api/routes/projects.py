from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_authorized_project, get_container
from app.api.schemas.projects import (
    AvailableProjectsRequest,
    CreateProjectRequest,
    CreateProjectResponse,
    ProjectMetadataResponse,
    ProjectResponse,
    RenameProjectRequest,
    UpdateProjectRequest,
)
from app.bootstrap import ApplicationContainer
from app.modules.projects.models import Project, ProjectAccessCredentials

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def metadata_response(project: Project) -> ProjectMetadataResponse:
    return ProjectMetadataResponse(
        project_id=project.id,
        name=project.name,
        updated_at=project.updated_at,
        expires_at=project.expires_at,
    )


@router.post("", response_model=CreateProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    container: ApplicationContainer = Depends(get_container),
) -> CreateProjectResponse:
    created_project = await container.project_service.create(request.name)
    project = created_project.project
    return CreateProjectResponse(
        project_id=project.id,
        project_token=created_project.project_token,
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


@router.post("/available", response_model=list[ProjectMetadataResponse])
async def get_available_projects(
    request: AvailableProjectsRequest,
    container: ApplicationContainer = Depends(get_container),
) -> list[ProjectMetadataResponse]:
    projects = await container.project_service.get_available(
        [
            ProjectAccessCredentials(
                project_id=item.project_id,
                project_token=item.project_token,
            )
            for item in request.projects
        ]
    )
    return [metadata_response(project) for project in projects]


@router.put("/{project_id}", response_model=ProjectMetadataResponse)
async def update_project(
    request: UpdateProjectRequest,
    project: Project = Depends(get_authorized_project),
    container: ApplicationContainer = Depends(get_container),
) -> ProjectMetadataResponse:
    updated_project = await container.project_service.update_document(
        project.id, request.document_xml
    )
    return metadata_response(updated_project)


@router.patch("/{project_id}", response_model=ProjectMetadataResponse)
async def rename_project(
    request: RenameProjectRequest,
    project: Project = Depends(get_authorized_project),
    container: ApplicationContainer = Depends(get_container),
) -> ProjectMetadataResponse:
    return metadata_response(await container.project_service.rename(project.id, request.name))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project: Project = Depends(get_authorized_project),
    container: ApplicationContainer = Depends(get_container),
) -> None:
    await container.project_service.delete(project.id)
