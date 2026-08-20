from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.sessions.enums import SessionStatus

DiagramIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9-]*$",
        description="Stable kebab-case identifier.",
    ),
]


class ApiSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class NextAction(StrEnum):
    WAIT = "wait"
    GET_QUESTIONS = "get_questions"
    GET_DIAGRAM = "get_diagram"
    CREATE_NEW_SESSION = "create_new_session"


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


class QuestionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    FREE_TEXT = "free_text"


class Question(ApiSchema):
    id: str
    text: str
    type: QuestionType
    required: bool
    options: list[str] = Field(default_factory=list)


class QuestionsResponse(ApiSchema):
    round: int = Field(ge=1)
    questions: list[Question]


class Answer(ApiSchema):
    question_id: str = Field(serialization_alias="questionId")
    value: str | list[str] | bool


class SubmitAnswersRequest(ApiSchema):
    round: int = Field(ge=1)
    answers: list[Answer]


class SubmitAnswersResponse(ApiSchema):
    status: SessionStatus


class ActorType(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class RelationType(StrEnum):
    ASSOCIATION = "association"
    INCLUDE = "include"
    EXTEND = "extend"
    GENERALIZATION = "generalization"


class Actor(ApiSchema):
    id: DiagramIdentifier
    name: str
    type: ActorType


class UseCase(ApiSchema):
    id: DiagramIdentifier
    name: str


class Relation(ApiSchema):
    type: RelationType
    source_id: DiagramIdentifier = Field(serialization_alias="sourceId")
    target_id: DiagramIdentifier = Field(serialization_alias="targetId")


class DiagramSystem(ApiSchema):
    id: DiagramIdentifier
    name: str


class Diagram(ApiSchema):
    schema_version: Literal["1.0"] = Field(serialization_alias="schemaVersion")
    system: DiagramSystem
    actors: list[Actor]
    use_cases: list[UseCase] = Field(serialization_alias="useCases")
    relations: list[Relation]
    assumptions: list[str]
    warnings: list[str]


class SessionStatusEvent(ApiSchema):
    status: SessionStatus


class ErrorBody(ApiSchema):
    code: str
    message: str


class ErrorResponse(ApiSchema):
    error: ErrorBody
