import structlog
from pydantic import ValidationError
from google import genai
from google.genai import types

from app.infrastructure.llm.client import (
    InvalidStructuredOutputError,
    LlmProviderError,
    ResponseModel,
)

logger = structlog.get_logger(__name__)


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
                    response_json_schema=response_schema.model_json_schema(),
                ),
            )
        except Exception as error:
            logger.error(
                "gemini_structured_request_failed",
                error_type=type(error).__name__,
                provider_error=str(error),
                response_schema=response_schema.__name__,
            )
            raise LlmProviderError(retryable=True) from error
        finally:
            client.close()
        if response.text is None:
            logger.error(
                "gemini_structured_response_empty",
                response_schema=response_schema.__name__,
            )
            raise InvalidStructuredOutputError()
        try:
            return response_schema.model_validate_json(response.text)
        except ValidationError as error:
            logger.error(
                "gemini_structured_response_invalid",
                response_schema=response_schema.__name__,
                validation_errors=_validation_errors(error),
            )
            raise InvalidStructuredOutputError() from error


def _validation_errors(error: ValidationError) -> list[dict[str, str]]:
    return [
        {
            "field": ".".join(str(part) for part in issue["loc"]),
            "message": issue["msg"],
            "rule": issue["type"],
        }
        for issue in error.errors(include_url=False)
    ]
