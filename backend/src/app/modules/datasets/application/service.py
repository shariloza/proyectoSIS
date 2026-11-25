"""Subida de archivos de entrenamiento: valida antes de aceptar y guarda versionado por hash."""

import hashlib
import io
import uuid
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.dataset import DatasetValidationError, prepare, read_csv
from app.modules.datasets.infrastructure.orm import DatasetRecord
from app.shared.errors import (
    ConflictError,
    InvalidInputError,
    NotFoundError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
)

ALLOWED_CONTENT_TYPES = frozenset({"text/csv", "application/vnd.ms-excel", "application/csv"})


class DatasetService:
    def __init__(self, session: Session, artifacts_dir: Path, max_bytes: int) -> None:
        self._session = session
        self._storage_dir = artifacts_dir / "datasets"
        self._max_bytes = max_bytes

    @property
    def max_bytes(self) -> int:
        return self._max_bytes

    def upload(
        self,
        filename: str,
        content_type: str | None,
        content: bytes,
        uploaded_by: uuid.UUID | None,
    ) -> DatasetRecord:
        if not filename.lower().endswith(".csv") or content_type not in ALLOWED_CONTENT_TYPES:
            raise UnsupportedMediaTypeError("Solo se aceptan archivos .csv (text/csv).")
        if len(content) > self._max_bytes:
            raise PayloadTooLargeError(
                f"El archivo supera el máximo de {self._max_bytes // (1024 * 1024)} MB."
            )

        sha256 = hashlib.sha256(content).hexdigest()
        existing = self._session.scalar(select(DatasetRecord).where(DatasetRecord.sha256 == sha256))
        if existing is not None:
            raise ConflictError(
                "Este archivo ya fue subido.", details={"dataset_id": str(existing.id)}
            )

        try:
            prepared = prepare(read_csv(io.BytesIO(content)))
        except DatasetValidationError as exc:
            raise InvalidInputError(
                "El archivo no cumple el formato esperado.", exc.problems
            ) from None

        self._storage_dir.mkdir(parents=True, exist_ok=True)
        stored = self._storage_dir / f"{sha256}.csv"
        stored.write_bytes(content)

        record = DatasetRecord(
            original_filename=Path(filename).name[:255],
            storage_path=str(Path("datasets") / stored.name),
            sha256=sha256,
            row_count=prepared.report.raw_rows,
            size_bytes=len(content),
            validation_report=asdict(prepared.report),
            uploaded_by=uploaded_by,
        )
        self._session.add(record)
        self._session.flush()
        return record

    def list(self) -> list[DatasetRecord]:
        return list(
            self._session.scalars(select(DatasetRecord).order_by(DatasetRecord.created_at.desc()))
        )

    def get(self, dataset_id: uuid.UUID) -> DatasetRecord:
        record = self._session.get(DatasetRecord, dataset_id)
        if record is None:
            raise NotFoundError("Dataset no encontrado.")
        return record
