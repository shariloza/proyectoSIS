from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import State
from app.api.errors import documented_errors
from app.modules.model_registry.application.service import ModelRegistryService
from app.shared.errors import AppError, ServiceUnavailableError

router = APIRouter(prefix="/health", tags=["Health"])


class HealthOut(BaseModel):
    status: Literal["ok"]
    model_version: str | None = None


@router.get("/live", summary="Liveness: el proceso responde", response_model=HealthOut)
def live() -> HealthOut:
    return HealthOut(status="ok")


@router.get(
    "/ready",
    summary="Readiness: base de datos accesible y modelo activo cargable",
    response_model=HealthOut,
    responses=documented_errors(503),
)
def ready(state: State) -> HealthOut:
    try:
        with state.sessions() as session:
            session.execute(text("SELECT 1"))
            active = ModelRegistryService(session).get_active()
            if active is None:
                raise ServiceUnavailableError("No hay un modelo activo.")
            loaded = state.models.get(active)
    except SQLAlchemyError:
        raise ServiceUnavailableError("La base de datos no responde.") from None
    except AppError as error:
        raise ServiceUnavailableError(error.message) from None
    return HealthOut(status="ok", model_version=loaded.version)
