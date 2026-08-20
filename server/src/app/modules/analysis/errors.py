from app.errors import AppError


class InvalidAnalysisResult(AppError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_analysis_result", "The analysis result does not meet the required contract"
        )


class InvalidAnswers(AppError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_answers", "The submitted answers do not match the current questions"
        )


class AnalysisProviderError(AppError):
    def __init__(self, retryable: bool) -> None:
        self.retryable = retryable
        super().__init__(
            "analysis_provider_error", "The analysis provider could not process the request"
        )
