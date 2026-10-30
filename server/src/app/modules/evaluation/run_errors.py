from app.errors import AppError


class EvaluationRunNotFound(AppError):
    def __init__(self) -> None:
        super().__init__("evaluation_run_not_found", "Evaluation run was not found")
