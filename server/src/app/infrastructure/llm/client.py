from typing import Protocol, TypeVar

from pydantic import BaseModel

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class LlmProviderError(Exception):
    def __init__(self, retryable: bool) -> None:
        self.retryable = retryable
        super().__init__("The LLM provider could not process the request")


class InvalidStructuredOutputError(Exception):
    pass


class StructuredLlmClient(Protocol):
    async def generate(
        self,
        prompt: str,
        response_schema: type[ResponseModel],
        system_instruction: str,
    ) -> ResponseModel: ...
