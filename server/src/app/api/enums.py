from enum import StrEnum


class NextAction(StrEnum):
    WAIT = "wait"
    GET_QUESTIONS = "get_questions"
    GET_DIAGRAM = "get_diagram"
    CREATE_NEW_SESSION = "create_new_session"
