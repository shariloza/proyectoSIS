from enum import StrEnum


class ModelStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class ActivationAction(StrEnum):
    ACTIVATE = "ACTIVATE"
    ROLLBACK = "ROLLBACK"
