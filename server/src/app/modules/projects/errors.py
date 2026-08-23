from app.errors import AppError


class ProjectNotFound(AppError):
    def __init__(self) -> None:
        super().__init__("project_not_found", "Project was not found or has expired")


class InvalidProjectToken(AppError):
    def __init__(self) -> None:
        super().__init__("invalid_project_token", "Project token is invalid")
