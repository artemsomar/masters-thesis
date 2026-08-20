from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types

from app.infrastructure.llm.client import (
    InvalidStructuredOutputError,
    LlmProviderError,
    ResponseModel,
)


class GeminiStructuredOutputClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def generate(
        self,
        prompt: str,
        response_schema: type[ResponseModel],
        system_instruction: str,
    ) -> ResponseModel:
        if not self._api_key or not self._model:
            raise LlmProviderError(retryable=False)
        client = genai.Client(api_key=self._api_key)
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
        except Exception as error:
            raise LlmProviderError(retryable=True) from error
        finally:
            client.close()
        if response.text is None:
            raise InvalidStructuredOutputError()
        try:
            return response_schema.model_validate_json(response.text)
        except ValidationError as error:
            raise InvalidStructuredOutputError() from error
