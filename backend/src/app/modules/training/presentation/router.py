import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.api.dependencies import Admin, training_service
from app.api.errors import documented_errors
from app.modules.model_registry.infrastructure.records import ModelVersionRecord
from app.modules.model_registry.presentation.router import ModelSummary
from app.modules.training.application.service import TrainingService
from app.modules.training.domain.job_status import JobStatus
from app.modules.training.infrastructure.records import TrainingJobRecord

router = APIRouter(prefix="/training-jobs", tags=["Re-entrenamiento"])


class TrainingJobCreate(BaseModel):
    dataset_id: uuid.UUID


class TrainingJobOut(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    status: JobStatus
    attempts: int
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    result_model: ModelSummary | None

    @classmethod
    def of(cls, job: TrainingJobRecord, model: ModelVersionRecord | None) -> "TrainingJobOut":
        return cls(
            id=job.id,
            dataset_id=job.dataset_id,
            status=JobStatus(job.status),
            attempts=job.attempts,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
            result_model=ModelSummary.of(model) if model else None,
        )


Service = Annotated[TrainingService, Depends(training_service)]


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar un re-entrenamiento (admin)",
    description=(
        "Crea un trabajo asíncrono que procesa el worker. El modelo resultante queda como "
        "APPROVED o REJECTED y nunca se activa solo. Solo puede haber un trabajo en curso."
    ),
    response_model=TrainingJobOut,
    responses=documented_errors(401, 403, 404, 409, 422),
)
def enqueue(body: TrainingJobCreate, admin: Admin, service: Service) -> TrainingJobOut:
    return TrainingJobOut.of(service.enqueue(body.dataset_id, admin.id), None)


@router.get(
    "",
    summary="Trabajos recientes (admin)",
    response_model=list[TrainingJobOut],
    responses=documented_errors(401, 403),
)
def recent(_: Admin, service: Service) -> list[TrainingJobOut]:
    return [TrainingJobOut.of(job, model) for job, model in service.recent()]


@router.get(
    "/{job_id}",
    summary="Estado de un re-entrenamiento (admin)",
    response_model=TrainingJobOut,
    responses=documented_errors(401, 403, 404),
)
def get_job(job_id: uuid.UUID, _: Admin, service: Service) -> TrainingJobOut:
    return TrainingJobOut.of(*service.get(job_id))
