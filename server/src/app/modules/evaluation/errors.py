from pathlib import Path

from app.errors import AppError


class EvaluationDatasetNotFound(AppError):
    def __init__(self, path: Path) -> None:
        super().__init__(
            "evaluation_dataset_not_found", f"Evaluation dataset was not found: {path}"
        )


class InvalidEvaluationDataset(AppError):
    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(
            "invalid_evaluation_dataset",
            f"Evaluation dataset is invalid at {path}: {reason}",
        )


class EvaluationDescriptionTooLong(AppError):
    def __init__(self, case_id: str) -> None:
        super().__init__(
            "evaluation_description_too_long",
            f"Evaluation case description exceeds the configured limit: {case_id}",
        )


class InvalidEmbeddingResult(AppError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_embedding_result", "The embedding provider returned an invalid result"
        )
