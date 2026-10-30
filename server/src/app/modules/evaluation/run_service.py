from datetime import UTC, datetime
from uuid import uuid4

from app.infrastructure.repositories.redis_evaluation_run_repository import (
    RedisEvaluationRunRepository,
)
from app.modules.evaluation.run_enums import EvaluationRunStatus
from app.modules.evaluation.run_errors import EvaluationRunNotFound
from app.modules.evaluation.run_models import EvaluationRun
from app.modules.evaluation.schemas import DiagramEvaluationResult


class EvaluationRunService:
    def __init__(self, repository: RedisEvaluationRunRepository) -> None:
        self._repository = repository

    async def create(self, limit: int | None) -> EvaluationRun:
        now = datetime.now(UTC)
        run = EvaluationRun(
            id=str(uuid4()),
            status=EvaluationRunStatus.PENDING,
            limit=limit,
            created_at=now,
            updated_at=now,
        )
        await self._repository.save(run)
        return run

    async def get(self, run_id: str) -> EvaluationRun:
        run = await self._repository.get(run_id)
        if run is None:
            raise EvaluationRunNotFound()
        return run

    async def set_current_job(self, run_id: str, job_id: str) -> EvaluationRun:
        run = await self.get(run_id)
        run.current_job_id = job_id
        run.updated_at = datetime.now(UTC)
        await self._repository.save(run)
        return run

    async def start(self, run_id: str) -> None:
        run = await self.get(run_id)
        run.status = EvaluationRunStatus.RUNNING
        run.updated_at = datetime.now(UTC)
        await self._repository.save(run)

    async def complete(self, run_id: str, results: list[DiagramEvaluationResult]) -> None:
        run = await self.get(run_id)
        run.status = EvaluationRunStatus.COMPLETED
        run.results = results
        run.updated_at = datetime.now(UTC)
        await self._repository.save(run)

    async def fail(self, run_id: str, error_code: str) -> None:
        run = await self.get(run_id)
        run.status = EvaluationRunStatus.FAILED
        run.error_code = error_code
        run.updated_at = datetime.now(UTC)
        await self._repository.save(run)
