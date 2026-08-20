from app.modules.diagrams.ports import DiagramGenerator
from app.modules.diagrams.schemas import Diagram, DiagramGenerationRequest
from app.modules.diagrams.validator import validate_diagram


class DiagramService:
    def __init__(self, generator: DiagramGenerator) -> None:
        self._generator = generator

    async def generate(self, request: DiagramGenerationRequest) -> Diagram:
        diagram = await self._generator.generate(request)
        validate_diagram(diagram)
        return diagram

    def deserialize(self, value: str) -> Diagram:
        diagram = Diagram.model_validate_json(value)
        validate_diagram(diagram)
        return diagram
