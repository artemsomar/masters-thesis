from app.errors import AppError


class InvalidClarificationResult(AppError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_clarification_result",
            "The clarification result does not meet the required contract",
        )
