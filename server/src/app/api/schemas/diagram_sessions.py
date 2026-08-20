from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

DiagramIdentifier = Annotated[
    str,
    Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9-]*$",
        description="Stable kebab-case identifier.",
    ),
]


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class DiagramSessionStatus(StrEnum):
    CREATED = "created"
    ANALYZING = "analyzing"
    AWAITING_ANSWERS = "awaiting_answers"
    GENERATING_DIAGRAM = "generating_diagram"
    DIAGRAM_READY = "diagram_ready"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class NextAction(StrEnum):
    WAIT = "wait"
    GET_QUESTIONS = "get_questions"
    GET_DIAGRAM = "get_diagram"
    CREATE_NEW_SESSION = "create_new_session"


class CreateDiagramSessionRequest(ApiModel):
    description: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=10)


class CreateDiagramSessionResponse(ApiModel):
    session_id: str = Field(serialization_alias="sessionId")
    session_token: str = Field(serialization_alias="sessionToken")
    status: DiagramSessionStatus
    expires_at: datetime = Field(serialization_alias="expiresAt")


class SessionStatusResponse(ApiModel):
    session_id: str = Field(serialization_alias="sessionId")
    status: DiagramSessionStatus
    next_action: NextAction = Field(serialization_alias="nextAction")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class QuestionType(StrEnum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    FREE_TEXT = "free_text"


class Question(ApiModel):
    id: str
    text: str
    type: QuestionType
    required: bool
    options: list[str] = Field(default_factory=list)


class QuestionsResponse(ApiModel):
    round: int = Field(ge=1)
    questions: list[Question]


class Answer(ApiModel):
    question_id: str = Field(serialization_alias="questionId")
    value: str | list[str] | bool


class SubmitAnswersRequest(ApiModel):
    round: int = Field(ge=1)
    answers: list[Answer]


class SubmitAnswersResponse(ApiModel):
    status: DiagramSessionStatus


class ActorType(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class RelationType(StrEnum):
    ASSOCIATION = "association"
    INCLUDE = "include"
    EXTEND = "extend"
    GENERALIZATION = "generalization"


class Actor(ApiModel):
    id: DiagramIdentifier
    name: str
    type: ActorType


class UseCase(ApiModel):
    id: DiagramIdentifier
    name: str


class Relation(ApiModel):
    type: RelationType
    source_id: DiagramIdentifier = Field(serialization_alias="sourceId")
    target_id: DiagramIdentifier = Field(serialization_alias="targetId")


class DiagramSystem(ApiModel):
    id: DiagramIdentifier
    name: str


class Diagram(ApiModel):
    schema_version: Literal["1.0"] = Field(serialization_alias="schemaVersion")
    system: DiagramSystem
    actors: list[Actor]
    use_cases: list[UseCase] = Field(serialization_alias="useCases")
    relations: list[Relation]
    assumptions: list[str]
    warnings: list[str]


class SessionStatusEvent(ApiModel):
    status: DiagramSessionStatus


class ErrorBody(ApiModel):
    code: str
    message: str


class ErrorResponse(ApiModel):
    error: ErrorBody
