from typing import Protocol

from app.modules.analysis.schemas import AnalysisAnswer, AnalysisResult


class RequirementsAnalyzer(Protocol):
    async def analyze(
        self,
        description: str,
        language: str,
        answers: list[AnalysisAnswer],
        allow_questions: bool,
    ) -> AnalysisResult: ...
