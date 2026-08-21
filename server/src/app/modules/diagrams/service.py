from app.infrastructure.llm.client import InvalidStructuredOutputError, StructuredLlmClient
from app.modules.diagrams.errors import InvalidDiagram
from app.modules.diagrams.prompts import SYSTEM_INSTRUCTION, build_diagram_prompt
from app.modules.diagrams.schemas import Diagram, DiagramGenerationOutput, DiagramGenerationRequest


class DiagramService:
    def __init__(self, llm_client: StructuredLlmClient) -> None:
        self._llm_client = llm_client

    async def generate(self, request: DiagramGenerationRequest) -> Diagram:
        try:
            generated = await self._llm_client.generate(
                build_diagram_prompt(request), DiagramGenerationOutput, SYSTEM_INSTRUCTION
            )
        except InvalidStructuredOutputError as error:
            raise InvalidDiagram() from error
        return Diagram.model_validate({"schema_version": "1.0", **generated.model_dump()})

    def deserialize(self, value: str) -> Diagram:
        return Diagram.model_validate_json(value)
