from app.infrastructure.llm.client import InvalidStructuredOutputError, StructuredLlmClient
from app.modules.diagrams.errors import InvalidDiagram
from app.modules.diagrams.prompts import SYSTEM_INSTRUCTION, build_diagram_prompt
from app.modules.diagrams.schemas import Diagram, DiagramGenerationRequest
from app.modules.diagrams.validator import validate_diagram


class DiagramService:
    def __init__(self, llm_client: StructuredLlmClient) -> None:
        self._llm_client = llm_client

    async def generate(self, request: DiagramGenerationRequest) -> Diagram:
        try:
            diagram = await self._llm_client.generate(
                build_diagram_prompt(request), Diagram, SYSTEM_INSTRUCTION
            )
        except InvalidStructuredOutputError as error:
            raise InvalidDiagram() from error
        validate_diagram(diagram)
        return diagram

    def deserialize(self, value: str) -> Diagram:
        diagram = Diagram.model_validate_json(value)
        validate_diagram(diagram)
        return diagram
