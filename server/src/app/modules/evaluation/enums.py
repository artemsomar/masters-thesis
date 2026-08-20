from enum import StrEnum


class EvaluationRelationType(StrEnum):
    ASSOCIATION = "association"
    INCLUDE = "include"
    EXTEND = "extend"
    GENERALIZATION = "generalization"
