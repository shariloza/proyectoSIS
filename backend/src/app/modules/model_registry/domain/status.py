from enum import StrEnum

from app.shared.errors import ConflictError


class ModelStatus(StrEnum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class ActivationAction(StrEnum):
    ACTIVATE = "ACTIVATE"
    ROLLBACK = "ROLLBACK"


# Solo un modelo aprobado, o uno que ya estuvo activo, puede volver a producción.
ACTIVATABLE = frozenset({ModelStatus.APPROVED, ModelStatus.RETIRED})


def ensure_can_activate(status: ModelStatus) -> None:
    if status == ModelStatus.ACTIVE:
        raise ConflictError("El modelo ya está activo.")
    if status not in ACTIVATABLE:
        raise ConflictError(
            f"Un modelo en estado {status} no puede activarse: "
            "solo los aprobados o retirados pueden pasar a producción."
        )
