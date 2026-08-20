from typing import TypeVar, cast

from pydantic import BaseModel

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


class FakeStructuredLlmClient:
    def __init__(self, result: BaseModel | Exception) -> None:
        self._result = result
        self.calls: list[tuple[str, type[BaseModel], str]] = []

    async def generate(
        self,
        prompt: str,
        response_schema: type[ResponseModel],
        system_instruction: str,
    ) -> ResponseModel:
        self.calls.append((prompt, response_schema, system_instruction))
        if isinstance(self._result, Exception):
            raise self._result
        return cast(ResponseModel, self._result)
