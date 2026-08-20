from pydantic import BaseModel, ConfigDict, Field

from app.modules.sessions.enums import SessionStatus


class SessionSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class Question(SessionSchema):
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-z][a-z0-9-]*$")
    text: str = Field(min_length=1, max_length=1_000)
    required: bool = True


class Answer(SessionSchema):
    question_id: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9-]*$",
        validation_alias="questionId",
        serialization_alias="questionId",
    )
    value: str = Field(min_length=1)


class ClarificationHistoryEntry(SessionSchema):
    round: int = Field(ge=1)
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class SessionStatusUpdate(SessionSchema):
    status: SessionStatus
    error_code: str | None = Field(default=None, serialization_alias="errorCode")
    correlation_id: str | None = Field(default=None, serialization_alias="correlationId")
