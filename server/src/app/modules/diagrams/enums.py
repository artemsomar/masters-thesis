from enum import StrEnum


class ActorType(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


class RelationType(StrEnum):
    ASSOCIATION = "association"
    INCLUDE = "include"
    EXTEND = "extend"
    GENERALIZATION = "generalization"
