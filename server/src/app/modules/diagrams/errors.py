from app.errors import AppError


class InvalidDiagram(AppError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_diagram", "The generated diagram does not meet the required contract"
        )


class InvalidFrameExtraction(AppError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            "invalid_frame_extraction", "The requirement frames do not meet the contract"
        )
        self.reason = reason


class InvalidLocalCorrection(AppError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            "invalid_local_correction", "The local correction does not meet the contract"
        )
        self.reason = reason
