from google import genai
from google.genai import types
from pydantic import ValidationError

from app.modules.diagrams.errors import DiagramProviderError, InvalidDiagram
from app.modules.diagrams.prompts import SYSTEM_INSTRUCTION, build_diagram_prompt
from app.modules.diagrams.schemas import Diagram, DiagramGenerationRequest


class GeminiDiagramGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, request: DiagramGenerationRequest) -> Diagram:
        if not self._api_key or not self._model:
            raise DiagramProviderError(retryable=False)
        client = genai.Client(api_key=self._api_key)
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=build_diagram_prompt(request),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=Diagram,
                ),
            )
        except Exception as error:
            raise DiagramProviderError(retryable=True) from error
        finally:
            client.close()
        if response.text is None:
            raise InvalidDiagram()
        try:
            return Diagram.model_validate_json(response.text)
        except ValidationError as error:
            raise InvalidDiagram() from error
