from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.api.enums import NextAction
from app.modules.diagrams.schemas import Diagram
from app.modules.sessions.enums import SessionStatus
from app.modules.sessions.schemas import Answer, Question


class ApiSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class CreateDiagramSessionRequest(ApiSchema):
    description: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=10)


class CreateDiagramSessionResponse(ApiSchema):
    session_id: str = Field(serialization_alias="sessionId")
    session_token: str = Field(serialization_alias="sessionToken")
    status: SessionStatus
    expires_at: datetime = Field(serialization_alias="expiresAt")


class SessionStatusResponse(ApiSchema):
    session_id: str = Field(serialization_alias="sessionId")
    status: SessionStatus
    next_action: NextAction = Field(serialization_alias="nextAction")
    updated_at: datetime = Field(serialization_alias="updatedAt")
    error_code: str | None = Field(default=None, serialization_alias="errorCode")


class QuestionsResponse(ApiSchema):
    round: int = Field(ge=1)
    questions: list[Question]


class SubmitAnswersRequest(ApiSchema):
    round: int = Field(ge=1)
    answers: list[Answer]


class SubmitAnswersResponse(ApiSchema):
    status: SessionStatus


class SessionStatusEvent(ApiSchema):
    status: SessionStatus
    error_code: str | None = Field(default=None, serialization_alias="errorCode")
    correlation_id: str | None = Field(default=None, serialization_alias="correlationId")


class DiagramPendingResponse(ApiSchema):
    status: SessionStatus


class ErrorBody(ApiSchema):
    code: str
    message: str


class ErrorResponse(ApiSchema):
    error: ErrorBody
