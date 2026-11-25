"""Caché en memoria del modelo activo. Se recarga sola cuando cambia la versión activa."""

import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from sklearn.pipeline import Pipeline

from app.ml.artifact import ArtifactError, load_model
from app.modules.model_registry.infrastructure.orm import ModelVersionRecord
from app.shared.errors import ServiceUnavailableError


@dataclass(frozen=True)
class LoadedModel:
    id: uuid.UUID
    version: str
    pipeline: Pipeline


class ActiveModelProvider:
    def __init__(self, artifacts_dir: Path) -> None:
        self._artifacts_dir = artifacts_dir
        self._loaded: LoadedModel | None = None
        self._lock = Lock()

    def get(self, active: ModelVersionRecord) -> LoadedModel:
        with self._lock:
            if self._loaded is None or self._loaded.id != active.id:
                try:
                    pipeline = load_model(
                        self._artifacts_dir / active.artifact_path,
                        active.artifact_sha256,
                        active.dependencies,
                    )
                except ArtifactError as exc:
                    raise ServiceUnavailableError(
                        "El modelo activo no pudo cargarse.", details=str(exc)
                    ) from exc
                self._loaded = LoadedModel(active.id, active.version, pipeline)
            return self._loaded
