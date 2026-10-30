from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_container
from app.api.schemas.evaluation_runs import (
    CreateEvaluationRunRequest,
    CreateEvaluationRunResponse,
    EvaluationRunStatusResponse,
)
from app.bootstrap import ApplicationContainer
from app.modules.evaluation.run_enums import EvaluationRunStatus

router = APIRouter(prefix="/api/v1/evaluation-runs", tags=["evaluation-runs"])


@router.post("", response_model=CreateEvaluationRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_evaluation_run(
    request: CreateEvaluationRunRequest,
    container: ApplicationContainer = Depends(get_container),
) -> CreateEvaluationRunResponse:
    run = await container.evaluation_run_workflow.create_run(request.limit)
    return CreateEvaluationRunResponse(run_id=run.id, status=run.status)


@router.get("/{run_id}", response_model=EvaluationRunStatusResponse)
async def get_evaluation_run(
    run_id: str,
    container: ApplicationContainer = Depends(get_container),
) -> EvaluationRunStatusResponse:
    run = await container.evaluation_run_service.get(run_id)
    return EvaluationRunStatusResponse(
        run_id=run.id,
        status=run.status,
        updated_at=run.updated_at,
        error_code=run.error_code,
        results=run.results if run.status is EvaluationRunStatus.COMPLETED else None,
    )
