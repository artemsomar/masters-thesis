from collections.abc import Iterable

from app.modules.sessions.errors import AnswerTooLong, DescriptionTooLong
from app.modules.sessions.schemas import Answer


def validate_description(description: str, max_length: int) -> None:
    if len(description) > max_length:
        raise DescriptionTooLong()


def validate_answers(answers: Iterable[Answer], max_length: int) -> None:
    if any(len(answer.value) > max_length for answer in answers):
        raise AnswerTooLong()
