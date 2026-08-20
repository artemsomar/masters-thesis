from typing import Protocol

from app.modules.diagrams.schemas import Diagram, DiagramGenerationRequest


class DiagramGenerator(Protocol):
    async def generate(self, request: DiagramGenerationRequest) -> Diagram: ...
