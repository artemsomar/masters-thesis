from dataclasses import dataclass

from app.config import Settings, get_settings
from app.logging_config import configure_logging


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    settings: Settings


def build_container(settings: Settings | None = None) -> ApplicationContainer:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    return ApplicationContainer(settings=resolved_settings)
