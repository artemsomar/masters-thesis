from app.errors import AppError


class InvalidDiagram(AppError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_diagram", "The generated diagram does not meet the required contract"
        )


class DiagramProviderError(AppError):
    def __init__(self, retryable: bool) -> None:
        self.retryable = retryable
        super().__init__(
            "diagram_provider_error", "The diagram provider could not process the request"
        )
