import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import Admin, registry_service
from app.api.errors import documented_errors
from app.modules.model_registry.application.service import ModelRegistryService
from app.modules.model_registry.domain.status import ModelStatus
from app.modules.model_registry.infrastructure.records import ModelVersionRecord

router = APIRouter(prefix="/models", tags=["Modelos"])


class ModelSummary(BaseModel):
    id: uuid.UUID
    version: str
    algorithm: str
    status: ModelStatus
    roc_auc: float = Field(description="ROC-AUC en el conjunto de test")
    f1_macro: float
    approved: bool = Field(description="¿Cumplió todos los criterios de aceptación?")
    trained_at: datetime
    activated_at: datetime | None

    @classmethod
    def of(cls, record: ModelVersionRecord) -> "ModelSummary":
        test = record.metrics["test"]
        return cls(
            id=record.id,
            version=record.version,
            algorithm=record.algorithm,
            status=ModelStatus(record.status),
            roc_auc=test["roc_auc"],
            f1_macro=test["f1_macro"],
            approved=record.acceptance_report["approved"],
            trained_at=record.trained_at,
            activated_at=record.activated_at,
        )


class ModelDetail(ModelSummary):
    dataset_id: uuid.UUID
    training_job_id: uuid.UUID | None
    hyperparameters: dict[str, Any]
    metrics: dict[str, Any] = Field(
        description="validation y test: métricas por clase, ROC-AUC, curva ROC, matriz de confusión"
    )
    acceptance: dict[str, Any] = Field(description="Resultado de cada criterio de aceptación")
    dependencies: dict[str, str]
    preprocessing_version: str
    random_seed: int
    artifact_sha256: str

    @classmethod
    def of(cls, record: ModelVersionRecord) -> "ModelDetail":
        return cls(
            **ModelSummary.of(record).model_dump(),
            dataset_id=record.dataset_id,
            training_job_id=record.training_job_id,
            hyperparameters=record.hyperparameters,
            metrics=record.metrics,
            acceptance=record.acceptance_report,
            dependencies=record.dependencies,
            preprocessing_version=record.preprocessing_version,
            random_seed=record.random_seed,
            artifact_sha256=record.artifact_sha256,
        )


Registry = Annotated[ModelRegistryService, Depends(registry_service)]


@router.get(
    "/active",
    summary="Métricas del modelo activo",
    description="Público: versión en producción con sus métricas de evaluación.",
    response_model=ModelDetail,
    responses=documented_errors(404),
)
def active_model(registry: Registry) -> ModelDetail:
    return ModelDetail.of(registry.require_active())


@router.get(
    "",
    summary="Listar versiones del modelo (admin)",
    response_model=list[ModelSummary],
    responses=documented_errors(401, 403),
)
def list_models(_: Admin, registry: Registry) -> list[ModelSummary]:
    return [ModelSummary.of(record) for record in registry.list()]


@router.get(
    "/{model_id}",
    summary="Detalle de una versión (admin)",
    response_model=ModelDetail,
    responses=documented_errors(401, 403, 404),
)
def get_model(model_id: uuid.UUID, _: Admin, registry: Registry) -> ModelDetail:
    return ModelDetail.of(registry.get(model_id))


@router.post(
    "/{model_id}/activate",
    summary="Activar una versión aprobada (admin)",
    description="Acción explícita: el modelo activo pasa a RETIRED y queda auditado.",
    response_model=ModelDetail,
    responses=documented_errors(401, 403, 404, 409),
)
def activate(model_id: uuid.UUID, admin: Admin, registry: Registry) -> ModelDetail:
    return ModelDetail.of(registry.activate(model_id, admin.id))


@router.post(
    "/rollback",
    summary="Volver a la versión activa anterior (admin)",
    response_model=ModelDetail,
    responses=documented_errors(401, 403, 409),
)
def rollback(admin: Admin, registry: Registry) -> ModelDetail:
    return ModelDetail.of(registry.rollback(admin.id))
