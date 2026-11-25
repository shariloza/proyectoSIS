"""Procesa los trabajos de re-entrenamiento de la cola (tabla training_jobs).

Cada entrenamiento corre en un proceso hijo con timeout: si se cuelga o falla, el
trabajo queda en TIMED_OUT/FAILED con su error, el artefacto parcial se elimina y el
modelo activo no se toca. El candidato resultante nunca se activa automáticamente.
"""

import dataclasses
import json
import logging
import multiprocessing
import shutil
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from app.machine_learning.artifact import METADATA_FILE, save_model
from app.machine_learning.dataset import prepare, read_csv
from app.machine_learning.evaluation import with_regression_check
from app.machine_learning.training import train
from app.modules.datasets.infrastructure.records import DatasetRecord
from app.modules.model_registry.application.service import ModelRegistryService
from app.modules.training.domain.job_status import JobStatus
from app.modules.training.infrastructure.records import TrainingJobRecord

logger = logging.getLogger(__name__)

HEARTBEAT_SECONDS = 5
MAX_ERROR_LENGTH = 2000


def train_and_save(
    dataset_path: Path, models_directory: Path, version: str, active_roc_auc: float | None
) -> dict[str, Any]:
    """Prepara, entrena, evalúa (incluido C9 si hay modelo activo) y guarda el artefacto."""
    prepared = prepare(read_csv(dataset_path))
    result = train(prepared.features, prepared.target)
    if active_roc_auc is not None:
        acceptance = with_regression_check(
            result.acceptance, result.test_metrics["roc_auc"], active_roc_auc
        )
        result = dataclasses.replace(result, acceptance=acceptance)
    return save_model(
        result,
        models_directory=models_directory,
        version_name=version,
        dataset_path=dataset_path,
        preparation=prepared.report,
    )


def _train_in_child_process(
    dataset_path: Path,
    models_directory: Path,
    version: str,
    active_roc_auc: float | None,
    errors: "multiprocessing.Queue[str]",
) -> None:
    try:
        train_and_save(dataset_path, models_directory, version, active_roc_auc)
    except Exception as error:
        errors.put(f"{type(error).__name__}: {error}"[:MAX_ERROR_LENGTH])
        raise SystemExit(1) from None


class TrainingWorker:
    def __init__(
        self, sessions: sessionmaker[Session], artifacts_directory: Path, timeout_seconds: int
    ) -> None:
        self._sessions = sessions
        self._artifacts_directory = artifacts_directory
        self._models_directory = artifacts_directory / "models"
        self._timeout = timeout_seconds

    def run_forever(
        self, poll_seconds: float, should_stop: Callable[[], bool], heartbeat_file: Path
    ) -> None:
        """Bucle principal. Toca `heartbeat_file` en cada vuelta (lo usa el healthcheck)."""
        logger.info("worker iniciado", extra={"timeout_seconds": self._timeout})
        while not should_stop():
            heartbeat_file.touch()
            if not self.run_once():
                time.sleep(poll_seconds)

    def run_once(self) -> bool:
        """Procesa como máximo un trabajo. Devuelve True si procesó alguno."""
        self.expire_stale_jobs()
        claimed = self._claim()
        if claimed is None:
            return False
        self._process(*claimed)
        return True

    def expire_stale_jobs(self) -> None:
        """Un RUNNING sin heartbeat reciente quedó huérfano (p. ej. el worker se reinició)."""
        limit = datetime.now(UTC) - timedelta(seconds=self._timeout + 4 * HEARTBEAT_SECONDS)
        with self._sessions.begin() as session:
            session.execute(
                update(TrainingJobRecord)
                .where(
                    TrainingJobRecord.status == JobStatus.RUNNING,
                    TrainingJobRecord.heartbeat_at < limit,
                )
                .values(
                    status=JobStatus.TIMED_OUT,
                    finished_at=datetime.now(UTC),
                    error_message="El trabajo quedó huérfano: sin heartbeat del worker.",
                )
            )

    def _claim(self) -> tuple[uuid.UUID, Path, uuid.UUID] | None:
        with self._sessions.begin() as session:
            job = session.scalar(
                select(TrainingJobRecord)
                .where(TrainingJobRecord.status == JobStatus.PENDING)
                .order_by(TrainingJobRecord.created_at)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            if job is None:
                return None
            now = datetime.now(UTC)
            job.status = JobStatus.RUNNING
            job.started_at = job.heartbeat_at = now
            job.attempts += 1
            dataset = session.get_one(DatasetRecord, job.dataset_id)
            return job.id, self._artifacts_directory / dataset.storage_path, dataset.id

    def _process(self, job_id: uuid.UUID, dataset_path: Path, dataset_id: uuid.UUID) -> None:
        with self._sessions() as session:
            registry = ModelRegistryService(session)
            version = registry.next_version_name()
            active = registry.get_active()
            active_roc_auc = active.metrics["test"]["roc_auc"] if active else None
        logger.info("entrenamiento iniciado", extra={"job_id": str(job_id), "version": version})

        error = self._run_with_timeout(job_id, dataset_path, version, active_roc_auc)
        if error is not None:
            status, message = error
            shutil.rmtree(self._models_directory / version, ignore_errors=True)
            self._finish(job_id, status, message)
            logger.warning(
                "entrenamiento sin éxito", extra={"job_id": str(job_id), "status": status}
            )
            return

        metadata_path = self._models_directory / version / METADATA_FILE
        metadata: dict[str, Any] = json.loads(metadata_path.read_text(encoding="utf-8"))
        try:
            with self._sessions.begin() as session:
                ModelRegistryService(session).register(
                    metadata, dataset_id=dataset_id, training_job_id=job_id
                )
                self._mark(session, job_id, JobStatus.SUCCEEDED, None)
        except Exception:
            shutil.rmtree(self._models_directory / version, ignore_errors=True)
            logger.exception("no se pudo registrar el modelo", extra={"job_id": str(job_id)})
            self._finish(job_id, JobStatus.FAILED, "No se pudo registrar la versión del modelo.")
            return
        logger.info(
            "entrenamiento terminado",
            extra={"job_id": str(job_id), "version": version, "status": metadata["status"]},
        )

    def _run_with_timeout(
        self, job_id: uuid.UUID, dataset_path: Path, version: str, active_roc_auc: float | None
    ) -> tuple[JobStatus, str] | None:
        context = multiprocessing.get_context("spawn")
        errors: multiprocessing.Queue[str] = context.Queue()
        process = context.Process(
            target=_train_in_child_process,
            args=(dataset_path, self._models_directory, version, active_roc_auc, errors),
            daemon=True,
        )
        process.start()
        deadline = time.monotonic() + self._timeout
        while process.is_alive() and (remaining := deadline - time.monotonic()) > 0:
            process.join(min(HEARTBEAT_SECONDS, remaining))
            self._heartbeat(job_id)

        if process.is_alive():
            process.terminate()
            process.join()
            return JobStatus.TIMED_OUT, f"Se superó el tiempo máximo de {self._timeout} s."
        if process.exitcode != 0:
            message = (
                errors.get(timeout=1)
                if not errors.empty()
                else f"El proceso de entrenamiento terminó con código {process.exitcode}."
            )
            return JobStatus.FAILED, message
        return None

    def _heartbeat(self, job_id: uuid.UUID) -> None:
        with self._sessions.begin() as session:
            session.execute(
                update(TrainingJobRecord)
                .where(TrainingJobRecord.id == job_id)
                .values(heartbeat_at=datetime.now(UTC))
            )

    def _finish(self, job_id: uuid.UUID, status: JobStatus, message: str | None) -> None:
        with self._sessions.begin() as session:
            self._mark(session, job_id, status, message)

    @staticmethod
    def _mark(session: Session, job_id: uuid.UUID, status: JobStatus, message: str | None) -> None:
        session.execute(
            update(TrainingJobRecord)
            .where(TrainingJobRecord.id == job_id)
            .values(status=status, error_message=message, finished_at=datetime.now(UTC))
        )
