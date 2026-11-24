import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.datasets.application.service import DatasetService
from app.modules.model_registry.infrastructure.orm import ModelVersionRecord
from app.modules.training.domain.job_status import ACTIVE_STATUSES
from app.modules.training.infrastructure.orm import TrainingJobRecord
from app.shared.errors import ConflictError, NotFoundError

RECENT_JOBS_LIMIT = 20


class TrainingService:
    def __init__(self, session: Session, datasets: DatasetService) -> None:
        self._session = session
        self._datasets = datasets

    def enqueue(self, dataset_id: uuid.UUID, requested_by: uuid.UUID) -> TrainingJobRecord:
        self._datasets.get(dataset_id)
        in_progress = self._session.scalar(
            select(TrainingJobRecord).where(TrainingJobRecord.status.in_(ACTIVE_STATUSES))
        )
        if in_progress is not None:
            raise ConflictError(
                "Ya hay un re-entrenamiento en curso.", details={"job_id": str(in_progress.id)}
            )
        job = TrainingJobRecord(dataset_id=dataset_id, requested_by=requested_by)
        self._session.add(job)
        self._session.flush()
        self._session.refresh(job)
        return job

    def get(self, job_id: uuid.UUID) -> tuple[TrainingJobRecord, ModelVersionRecord | None]:
        job = self._session.get(TrainingJobRecord, job_id)
        if job is None:
            raise NotFoundError("Trabajo de re-entrenamiento no encontrado.")
        return job, self._result_of(job.id)

    def recent(self) -> list[tuple[TrainingJobRecord, ModelVersionRecord | None]]:
        jobs = self._session.scalars(
            select(TrainingJobRecord)
            .order_by(TrainingJobRecord.created_at.desc())
            .limit(RECENT_JOBS_LIMIT)
        )
        return [(job, self._result_of(job.id)) for job in jobs]

    def _result_of(self, job_id: uuid.UUID) -> ModelVersionRecord | None:
        return self._session.scalar(
            select(ModelVersionRecord).where(ModelVersionRecord.training_job_id == job_id)
        )
