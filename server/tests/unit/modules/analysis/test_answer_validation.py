import pytest

from app.modules.analysis.errors import InvalidAnswers
from app.modules.analysis.schemas import AnalysisAnswer, AnalysisQuestion, AnalysisResult
from app.modules.analysis.service import RequirementsAnalysisService
from tests.fakes.fake_sessions import FakeRequirementsAnalyzer


@pytest.mark.unit
def test_required_answers_must_match_the_current_questions() -> None:
    service = RequirementsAnalysisService(FakeRequirementsAnalyzer(AnalysisResult()), 7)

    with pytest.raises(InvalidAnswers):
        service.validate_answers(
            [AnalysisQuestion(id="booking-channel", text="How is booking confirmed?")],
            [AnalysisAnswer(question_id="unknown", value="By email")],
        )
