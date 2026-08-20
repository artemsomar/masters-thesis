from app.modules.sessions.errors import InvalidAnswers
from app.modules.sessions.schemas import Answer, Question


def validate_answer_submission(questions: list[Question], answers: list[Answer]) -> None:
    question_ids = {question.id for question in questions}
    answer_ids = {answer.question_id for answer in answers}
    if len(answer_ids) != len(answers) or not answer_ids <= question_ids:
        raise InvalidAnswers()
    if any(question.required and question.id not in answer_ids for question in questions):
        raise InvalidAnswers()
