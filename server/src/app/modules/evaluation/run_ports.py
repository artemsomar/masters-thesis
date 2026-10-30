from typing import Protocol


class EvaluationRunJobDispatcher(Protocol):
    def dispatch_evaluation_run(self, run_id: str, job_id: str) -> None: ...
