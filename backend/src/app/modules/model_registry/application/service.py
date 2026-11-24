"""Registro de versiones, activación y rollback (todo en transacciones atómicas)."""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.artifact import MODEL_FILE
from app.modules.model_registry.domain.status import (
    ActivationAction,
    ModelStatus,
    ensure_can_activate,
)
from app.modules.model_registry.infrastructure.orm import (
    ModelActivationEventRecord,
    ModelVersionRecord,
)
from app.shared.errors import ConflictError, NotFoundError


class ModelRegistryService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def next_version_name(self) -> str:
        count = self._session.scalar(select(func.count()).select_from(ModelVersionRecord))
        return f"v{(count or 0) + 1}"

    def register(
        self,
        metadata: dict[str, Any],
        *,
        dataset_id: uuid.UUID,
        training_job_id: uuid.UUID | None,
    ) -> ModelVersionRecord:
        record = ModelVersionRecord(
            version=metadata["version"],
            dataset_id=dataset_id,
            training_job_id=training_job_id,
            algorithm=metadata["algorithm"],
            hyperparameters=metadata["hyperparameters"],
            metrics=metadata["metrics"],
            acceptance_report=metadata["acceptance"],
            dependencies=metadata["dependencies"],
            preprocessing_version=metadata["preprocessing_version"],
            random_seed=metadata["random_seed"],
            artifact_path=str(Path("models") / metadata["version"] / MODEL_FILE),
            artifact_sha256=metadata["artifact"]["sha256"],
            status=metadata["status"],
            trained_at=datetime.fromisoformat(metadata["trained_at"]),
        )
        self._session.add(record)
        self._session.flush()
        return record

    def list(self) -> list[ModelVersionRecord]:
        return list(
            self._session.scalars(
                select(ModelVersionRecord).order_by(ModelVersionRecord.trained_at.desc())
            )
        )

    def get(self, model_id: uuid.UUID) -> ModelVersionRecord:
        record = self._session.get(ModelVersionRecord, model_id)
        if record is None:
            raise NotFoundError("Versión de modelo no encontrada.")
        return record

    def get_active(self) -> ModelVersionRecord | None:
        return self._session.scalar(
            select(ModelVersionRecord).where(ModelVersionRecord.status == ModelStatus.ACTIVE)
        )

    def require_active(self) -> ModelVersionRecord:
        active = self.get_active()
        if active is None:
            raise NotFoundError("No hay un modelo activo.")
        return active

    def activate(self, model_id: uuid.UUID, performed_by: uuid.UUID) -> ModelVersionRecord:
        target = self._lock(model_id)
        ensure_can_activate(ModelStatus(target.status))
        return self._switch_to(target, performed_by, ActivationAction.ACTIVATE)

    def rollback(self, performed_by: uuid.UUID) -> ModelVersionRecord:
        """Reactiva el modelo que estaba activo antes de la última activación."""
        last_event = self._session.scalar(
            select(ModelActivationEventRecord).order_by(ModelActivationEventRecord.id.desc())
        )
        if last_event is None or last_event.previous_model_version_id is None:
            raise ConflictError("No hay una versión anterior a la cual volver.")
        target = self._lock(last_event.previous_model_version_id)
        ensure_can_activate(ModelStatus(target.status))
        return self._switch_to(target, performed_by, ActivationAction.ROLLBACK)

    def _switch_to(
        self, target: ModelVersionRecord, performed_by: uuid.UUID, action: ActivationAction
    ) -> ModelVersionRecord:
        current = self._session.scalar(
            select(ModelVersionRecord)
            .where(ModelVersionRecord.status == ModelStatus.ACTIVE)
            .with_for_update()
        )
        if current is not None:
            current.status = ModelStatus.RETIRED
            self._session.flush()  # libera el índice único antes de activar el nuevo
        target.status = ModelStatus.ACTIVE
        target.activated_at = datetime.now(UTC)
        self._session.add(
            ModelActivationEventRecord(
                model_version_id=target.id,
                previous_model_version_id=current.id if current else None,
                action=action,
                performed_by=performed_by,
            )
        )
        self._session.flush()
        return target

    def _lock(self, model_id: uuid.UUID) -> ModelVersionRecord:
        record = self._session.get(ModelVersionRecord, model_id, with_for_update=True)
        if record is None:
            raise NotFoundError("Versión de modelo no encontrada.")
        return record
