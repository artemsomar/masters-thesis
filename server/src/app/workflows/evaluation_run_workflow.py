from itertools import islice
from pathlib import Path
from uuid import uuid4

import structlog
from app.errors import AppError
from app.infrastructure.llm.client import LlmProviderError
from app.modules.evaluation.run_enums import EvaluationRunStatus
from app.modules.evaluation.run_models import EvaluationRun
from app.modules.evaluation.run_ports import EvaluationRunJobDispatcher
from app.modules.evaluation.run_service import EvaluationRunService
from app.modules.evaluation.service import EvaluationService
from app.workflows.evaluation_workflow import EvaluationWorkflow

logger = structlog.get_logger(__name__)

_PROCESSABLE_STATUSES = {EvaluationRunStatus.PENDING, EvaluationRunStatus.RUNNING}


class EvaluationRunWorkflow:
    def __init__(
        self,
        run_service: EvaluationRunService,
        job_dispatcher: EvaluationRunJobDispatcher,
        evaluation_service: EvaluationService,
        evaluation_workflow: EvaluationWorkflow,
        dataset_path: Path,
    ) -> None:
        self._run_service = run_service
        self._job_dispatcher = job_dispatcher
        self._evaluation_service = evaluation_service
        self._evaluation_workflow = evaluation_workflow
        self._dataset_path = dataset_path

    async def create_run(self, limit: int | None) -> EvaluationRun:
        run = await self._run_service.create(limit)
        job_id = str(uuid4())
        run = await self._run_service.set_current_job(run.id, job_id)
        try:
            self._job_dispatcher.dispatch_evaluation_run(run.id, job_id)
        except Exception:
            await self._run_service.fail(run.id, "evaluation_run_processing_failed")
            raise
        return run

    async def process_run(self, run_id: str) -> None:
        run = await self._run_service.get(run_id)
        if run.status not in _PROCESSABLE_STATUSES:
            return
        await self._run_service.start(run_id)
        logger.info("evaluation_run_processing_started", run_id=run_id, limit=run.limit)
        try:
            cases = self._evaluation_service.load_cases(self._dataset_path)
            results = [
                await self._evaluation_workflow.evaluate_case(case)
                for case in islice(cases, run.limit)
            ]
        except LlmProviderError as error:
            if error.retryable:
                logger.warning("evaluation_run_retry_scheduled", run_id=run_id)
                raise
            logger.warning("evaluation_run_failed", run_id=run_id)
            await self._run_service.fail(run_id, "evaluation_run_processing_failed")
            return
        except AppError:
            logger.warning("evaluation_run_dataset_invalid", run_id=run_id)
            await self._run_service.fail(run_id, "evaluation_run_processing_failed")
            return
        await self._run_service.complete(run_id, results)
        logger.info("evaluation_run_processing_completed", run_id=run_id, case_count=len(results))
