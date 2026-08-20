from google import genai
from google.genai import types
from pydantic import ValidationError

from app.modules.analysis.errors import AnalysisProviderError, InvalidAnalysisResult
from app.modules.analysis.prompts import SYSTEM_INSTRUCTION, build_analysis_prompt
from app.modules.analysis.schemas import AnalysisAnswer, AnalysisResult


class GeminiRequirementsAnalyzer:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def analyze(
        self,
        description: str,
        language: str,
        answers: list[AnalysisAnswer],
        allow_questions: bool,
    ) -> AnalysisResult:
        if not self._api_key or not self._model:
            raise AnalysisProviderError(retryable=False)
        client = genai.Client(api_key=self._api_key)
        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=build_analysis_prompt(description, language, answers, allow_questions),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=AnalysisResult,
                ),
            )
        except Exception as error:
            raise AnalysisProviderError(retryable=True) from error
        finally:
            client.close()
        if response.text is None:
            raise InvalidAnalysisResult()
        try:
            return AnalysisResult.model_validate_json(response.text)
        except ValidationError as error:
            raise InvalidAnalysisResult() from error
