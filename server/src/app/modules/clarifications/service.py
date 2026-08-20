from app.infrastructure.llm.client import InvalidStructuredOutputError, StructuredLlmClient
from app.modules.clarifications.errors import InvalidClarificationResult
from app.modules.clarifications.prompts import SYSTEM_INSTRUCTION, build_clarification_prompt
from app.modules.clarifications.schemas import ClarificationResult


class ClarificationService:
    def __init__(self, llm_client: StructuredLlmClient, max_questions_per_round: int) -> None:
        self._llm_client = llm_client
        self._max_questions_per_round = max_questions_per_round

    async def ask(self, description: str, language: str, history: str) -> ClarificationResult:
        try:
            result = await self._llm_client.generate(
                build_clarification_prompt(description, language, history),
                ClarificationResult,
                SYSTEM_INSTRUCTION,
            )
        except InvalidStructuredOutputError as error:
            raise InvalidClarificationResult() from error
        self._validate_result(result)
        return result

    def _validate_result(self, result: ClarificationResult) -> None:
        question_ids = [question.id for question in result.questions]
        if len(question_ids) != len(set(question_ids)):
            raise InvalidClarificationResult()
        if len(result.questions) > self._max_questions_per_round:
            raise InvalidClarificationResult()
