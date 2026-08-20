from app.errors import AppError


class InvalidDiagram(AppError):
    def __init__(self) -> None:
        super().__init__(
            "invalid_diagram", "The generated diagram does not meet the required contract"
        )
