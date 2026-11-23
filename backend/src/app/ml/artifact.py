"""Persistencia de modelos: artefacto inmutable + metadatos de la sección 6.2 de la base."""

import json
import platform
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

from app.ml.dataset import PreparationReport, file_sha256
from app.ml.schema import FEATURE_COLUMNS, PREPROCESSING_VERSION
from app.ml.training import RANDOM_SEED, TrainingResult

MODEL_FILE = "model.joblib"
METADATA_FILE = "metadata.json"
# Librerías cuya versión debe coincidir para cargar un artefacto de forma segura.
PINNED_LIBRARIES = ("scikit-learn", "numpy", "pandas", "joblib")


class ArtifactError(RuntimeError):
    """El artefacto no existe, está alterado o es incompatible con el entorno actual."""


def runtime_dependencies() -> dict[str, str]:
    return {"python": platform.python_version()} | {lib: version(lib) for lib in PINNED_LIBRARIES}


def save_model(
    result: TrainingResult,
    *,
    models_dir: Path,
    version_name: str,
    dataset_path: Path,
    preparation: PreparationReport,
) -> dict[str, Any]:
    """Guarda el modelo en `<models_dir>/<version>/`. Nunca sobrescribe una versión."""
    target_dir = models_dir / version_name
    if target_dir.exists():
        raise ArtifactError(f"la versión {version_name} ya existe; las versiones son inmutables")
    target_dir.mkdir(parents=True)

    model_path = target_dir / MODEL_FILE
    joblib.dump(result.model, model_path)
    metadata = {
        "version": version_name,
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "status": "APPROVED" if result.acceptance["approved"] else "REJECTED",
        "algorithm": result.algorithm,
        "hyperparameters": result.hyperparameters,
        "random_seed": RANDOM_SEED,
        "preprocessing_version": PREPROCESSING_VERSION,
        "feature_columns": list(FEATURE_COLUMNS),
        "dataset": {
            "filename": dataset_path.name,
            "sha256": file_sha256(dataset_path),
            "preparation": asdict(preparation),
            "split_sizes": result.split_sizes,
        },
        "metrics": {"validation": result.validation_metrics, "test": result.test_metrics},
        "comparison": result.comparison,
        "acceptance": result.acceptance,
        "dependencies": runtime_dependencies(),
        "artifact": {"file": MODEL_FILE, "sha256": file_sha256(model_path)},
    }
    (target_dir / METADATA_FILE).write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metadata


def load_model(model_path: Path, expected_sha256: str, dependencies: dict[str, str]) -> Pipeline:
    """Carga un artefacto verificando integridad (hash) y compatibilidad de librerías."""
    if not model_path.is_file():
        raise ArtifactError(f"no existe el artefacto {model_path}")
    if file_sha256(model_path) != expected_sha256:
        raise ArtifactError(f"el hash de {model_path} no coincide: artefacto alterado")

    current = runtime_dependencies()
    mismatched = [
        f"{lib} {dependencies.get(lib)} != {current[lib]}"
        for lib in PINNED_LIBRARIES
        if dependencies.get(lib) != current[lib]
    ]
    if mismatched:
        raise ArtifactError("artefacto incompatible con el entorno: " + ", ".join(mismatched))

    model = joblib.load(model_path)
    if not isinstance(model, Pipeline):
        raise ArtifactError("el artefacto no contiene un Pipeline de scikit-learn")
    return model
