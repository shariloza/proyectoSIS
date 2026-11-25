from pathlib import Path
from typing import Any

import pytest

from app.ml.artifact import (
    METADATA_FILE,
    MODEL_FILE,
    ArtifactError,
    load_model,
    save_model,
)
from app.ml.dataset import PreparedDataset
from app.ml.training import Candidate, train
from tests.ml.conftest import DATASET_PATH


@pytest.fixture
def saved(
    tmp_path: Path, prepared: PreparedDataset, fast_candidates: list[Candidate]
) -> dict[str, Any]:
    result = train(prepared.features, prepared.target, fast_candidates)
    return save_model(
        result,
        models_dir=tmp_path,
        version_name="v-test",
        dataset_path=DATASET_PATH,
        preparation=prepared.report,
    )


def test_metadata_contains_everything_required_by_section_6_2(
    saved: dict[str, Any], tmp_path: Path
) -> None:
    required = {
        "version",
        "trained_at",
        "dataset",
        "algorithm",
        "hyperparameters",
        "metrics",
        "dependencies",
        "artifact",
        "status",
        "random_seed",
        "preprocessing_version",
    }
    assert required <= saved.keys()
    assert len(saved["dataset"]["sha256"]) == 64
    assert len(saved["artifact"]["sha256"]) == 64
    assert (tmp_path / "v-test" / METADATA_FILE).is_file()


def test_roundtrip_gives_identical_predictions(
    tmp_path: Path, prepared: PreparedDataset, fast_candidates: list[Candidate]
) -> None:
    result = train(prepared.features, prepared.target, fast_candidates)
    metadata = save_model(
        result,
        models_dir=tmp_path,
        version_name="v-roundtrip",
        dataset_path=DATASET_PATH,
        preparation=prepared.report,
    )

    reloaded = load_model(
        tmp_path / "v-roundtrip" / MODEL_FILE,
        metadata["artifact"]["sha256"],
        metadata["dependencies"],
    )

    rows = prepared.features.head(20)
    assert (result.model.predict_proba(rows) == reloaded.predict_proba(rows)).all()


def test_versions_are_immutable(
    saved: dict[str, Any],
    tmp_path: Path,
    prepared: PreparedDataset,
    fast_candidates: list[Candidate],
) -> None:
    result = train(prepared.features, prepared.target, fast_candidates)

    with pytest.raises(ArtifactError, match="inmutables"):
        save_model(
            result,
            models_dir=tmp_path,
            version_name="v-test",
            dataset_path=DATASET_PATH,
            preparation=prepared.report,
        )


def test_tampered_artifact_is_rejected(saved: dict[str, Any], tmp_path: Path) -> None:
    model_path = tmp_path / "v-test" / MODEL_FILE
    model_path.write_bytes(model_path.read_bytes() + b"tampered")

    with pytest.raises(ArtifactError, match="alterado"):
        load_model(model_path, saved["artifact"]["sha256"], saved["dependencies"])


def test_incompatible_library_version_is_rejected(saved: dict[str, Any], tmp_path: Path) -> None:
    dependencies = saved["dependencies"] | {"scikit-learn": "0.24.0"}

    with pytest.raises(ArtifactError, match=r"incompatible.*scikit-learn"):
        load_model(tmp_path / "v-test" / MODEL_FILE, saved["artifact"]["sha256"], dependencies)


def test_missing_artifact_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ArtifactError, match="no existe"):
        load_model(tmp_path / "nope.joblib", "0" * 64, {})
