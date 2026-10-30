import json
from datetime import datetime

from redis.asyncio import Redis

from app.modules.evaluation.run_enums import EvaluationRunStatus
from app.modules.evaluation.run_models import EvaluationRun
from app.modules.evaluation.schemas import DiagramEvaluationResult


class RedisEvaluationRunRepository:
    def __init__(self, client: Redis, ttl_seconds: int) -> None:
        self._client = client
        self._ttl_seconds = ttl_seconds

    async def get(self, run_id: str) -> EvaluationRun | None:
        value = await self._client.get(self._key(run_id))
        if value is None:
            return None
        return self._deserialize(value)

    async def save(self, run: EvaluationRun) -> None:
        await self._client.set(self._key(run.id), self._serialize(run), ex=self._ttl_seconds)

    def _key(self, run_id: str) -> str:
        return f"evaluation-run:{run_id}"

    def _serialize(self, run: EvaluationRun) -> str:
        return json.dumps(
            {
                "runId": run.id,
                "status": run.status,
                "limit": run.limit,
                "currentJobId": run.current_job_id,
                "results": [result.model_dump(mode="json") for result in run.results],
                "errorCode": run.error_code,
                "createdAt": run.created_at.isoformat(),
                "updatedAt": run.updated_at.isoformat(),
            }
        )

    def _deserialize(self, value: bytes | str) -> EvaluationRun:
        payload = json.loads(value)
        return EvaluationRun(
            id=payload["runId"],
            status=EvaluationRunStatus(payload["status"]),
            limit=payload.get("limit"),
            current_job_id=payload.get("currentJobId"),
            results=[
                DiagramEvaluationResult.model_validate(item)
                for item in payload.get("results", [])
            ],
            error_code=payload.get("errorCode"),
            created_at=datetime.fromisoformat(payload["createdAt"]),
            updated_at=datetime.fromisoformat(payload["updatedAt"]),
        )
