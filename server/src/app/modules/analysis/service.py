from app.modules.analysis.errors import InvalidAnalysisResult, InvalidAnswers
from app.modules.analysis.ports import RequirementsAnalyzer
from app.modules.analysis.schemas import AnalysisAnswer, AnalysisQuestion, AnalysisResult


class RequirementsAnalysisService:
    def __init__(self, analyzer: RequirementsAnalyzer, max_questions_per_round: int) -> None:
        self._analyzer = analyzer
        self._max_questions_per_round = max_questions_per_round

    async def analyze(
        self,
        description: str,
        language: str,
        answers: list[AnalysisAnswer],
        allow_questions: bool,
    ) -> AnalysisResult:
        result = await self._analyzer.analyze(description, language, answers, allow_questions)
        if not allow_questions:
            result = result.model_copy(update={"questions": []})
        self._validate_result(result, allow_questions)
        return result

    def validate_answers(
        self, questions: list[AnalysisQuestion], answers: list[AnalysisAnswer]
    ) -> None:
        question_ids = {question.id for question in questions}
        answer_ids = {answer.question_id for answer in answers}
        if len(answer_ids) != len(answers) or not answer_ids <= question_ids:
            raise InvalidAnswers()
        if any(question.required and question.id not in answer_ids for question in questions):
            raise InvalidAnswers()

    def _validate_result(self, result: AnalysisResult, allow_questions: bool) -> None:
        question_ids = [question.id for question in result.questions]
        if len(question_ids) != len(set(question_ids)):
            raise InvalidAnalysisResult()
        if len(result.questions) > self._max_questions_per_round:
            raise InvalidAnalysisResult()
