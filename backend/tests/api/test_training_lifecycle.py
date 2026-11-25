"""Ciclo completo: subir dataset → re-entrenar (worker real) → activar → rollback."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.api.dependencies import AppState
from app.modules.model_registry.infrastructure.records import ModelVersionRecord
from app.modules.training.application.worker import TrainingWorker
from tests.api.conftest import VALID_PROFILE
from tests.api.test_datasets import sample_csv_bytes, upload

pytestmark = pytest.mark.integration

JOBS = "/api/v1/training-jobs"


def worker(state: AppState, timeout_seconds: int = 300) -> TrainingWorker:
    return TrainingWorker(state.sessions, state.settings.artifacts_directory, timeout_seconds)


def new_dataset(client: TestClient, headers: dict[str, str], seed: int) -> str:
    response = upload(client, headers, sample_csv_bytes(1200, seed=seed))
    assert response.status_code == 201, response.text
    dataset_id: str = response.json()["id"]
    return dataset_id


def test_retraining_produces_candidate_that_is_not_activated(
    client: TestClient, admin_headers: dict[str, str], state: AppState
) -> None:
    dataset_id = new_dataset(client, admin_headers, seed=31)

    created = client.post(JOBS, json={"dataset_id": dataset_id}, headers=admin_headers)
    assert created.status_code == 202
    assert created.json()["status"] == "PENDING"

    duplicate = client.post(JOBS, json={"dataset_id": dataset_id}, headers=admin_headers)
    assert duplicate.status_code == 409

    assert worker(state).run_once() is True

    job = client.get(f"{JOBS}/{created.json()['id']}", headers=admin_headers).json()
    assert job["status"] == "SUCCEEDED", job["error_message"]
    candidate = job["result_model"]
    assert candidate["status"] in ("APPROVED", "REJECTED")
    assert client.get("/api/v1/models/active").json()["version"] == "v1"

    detail = client.get(f"/api/v1/models/{candidate['id']}", headers=admin_headers).json()
    assert detail["acceptance"]["criteria"][-1]["code"] == "C9"


def test_activation_and_rollback(
    client: TestClient, admin_headers: dict[str, str], state: AppState
) -> None:
    models = client.get("/api/v1/models", headers=admin_headers).json()
    candidate = next(m for m in models if m["version"] != "v1")
    # Se fuerza APPROVED para probar la activación independientemente de las métricas.
    with state.sessions.begin() as session:
        session.execute(
            update(ModelVersionRecord)
            .where(ModelVersionRecord.id == uuid.UUID(candidate["id"]))
            .values(status="APPROVED")
        )

    activated = client.post(f"/api/v1/models/{candidate['id']}/activate", headers=admin_headers)
    assert activated.status_code == 200
    assert client.get("/api/v1/models/active").json()["id"] == candidate["id"]
    prediction = client.post("/api/v1/predictions", json=VALID_PROFILE).json()
    assert prediction["model_version"] == candidate["version"]

    again = client.post(f"/api/v1/models/{candidate['id']}/activate", headers=admin_headers)
    assert again.status_code == 409

    rolled_back = client.post("/api/v1/models/rollback", headers=admin_headers)
    assert rolled_back.status_code == 200
    assert rolled_back.json()["version"] == "v1"
    statuses = {
        m["version"]: m["status"]
        for m in client.get("/api/v1/models", headers=admin_headers).json()
    }
    assert statuses["v1"] == "ACTIVE"
    assert statuses[candidate["version"]] == "RETIRED"


def test_rejected_model_cannot_be_activated(
    client: TestClient, admin_headers: dict[str, str], state: AppState
) -> None:
    models = client.get("/api/v1/models", headers=admin_headers).json()
    target = next(m for m in models if m["status"] != "ACTIVE")
    with state.sessions.begin() as session:
        session.execute(
            update(ModelVersionRecord)
            .where(ModelVersionRecord.id == uuid.UUID(target["id"]))
            .values(status="REJECTED")
        )

    response = client.post(f"/api/v1/models/{target['id']}/activate", headers=admin_headers)

    assert response.status_code == 409
    assert client.get("/api/v1/models/active").json()["version"] == "v1"


def test_failed_training_keeps_active_model(
    client: TestClient, admin_headers: dict[str, str], state: AppState
) -> None:
    dataset_id = new_dataset(client, admin_headers, seed=32)
    datasets = client.get("/api/v1/datasets", headers=admin_headers).json()
    stored = next(d for d in datasets if d["id"] == dataset_id)
    # Se corrompe el archivo en disco después de aceptado: el entrenamiento debe fallar.
    (state.settings.artifacts_directory / "datasets" / f"{stored['sha256']}.csv").write_text(
        "x\n1\n"
    )
    job_id = client.post(JOBS, json={"dataset_id": dataset_id}, headers=admin_headers).json()["id"]

    worker(state).run_once()

    job = client.get(f"{JOBS}/{job_id}", headers=admin_headers).json()
    assert job["status"] == "FAILED"
    assert "DatasetValidationError" in job["error_message"]
    assert job["result_model"] is None
    assert client.get("/api/v1/models/active").json()["version"] == "v1"
    assert client.get("/api/v1/health/ready").status_code == 200


def test_training_timeout_is_enforced(
    client: TestClient, admin_headers: dict[str, str], state: AppState
) -> None:
    dataset_id = new_dataset(client, admin_headers, seed=33)
    job_id = client.post(JOBS, json={"dataset_id": dataset_id}, headers=admin_headers).json()["id"]

    worker(state, timeout_seconds=1).run_once()

    job = client.get(f"{JOBS}/{job_id}", headers=admin_headers).json()
    assert job["status"] == "TIMED_OUT"
    assert client.get("/api/v1/models/active").json()["version"] == "v1"


def test_unknown_job_and_dataset(client: TestClient, admin_headers: dict[str, str]) -> None:
    unknown = str(uuid.uuid4())

    assert client.get(f"{JOBS}/{unknown}", headers=admin_headers).status_code == 404
    response = client.post(JOBS, json={"dataset_id": unknown}, headers=admin_headers)
    assert response.status_code == 404


def test_admin_endpoints_require_token(client: TestClient) -> None:
    some_id = str(uuid.uuid4())
    for method, url in [
        ("get", "/api/v1/models"),
        ("get", f"/api/v1/models/{some_id}"),
        ("post", f"/api/v1/models/{some_id}/activate"),
        ("post", "/api/v1/models/rollback"),
        ("get", JOBS),
        ("get", "/api/v1/datasets"),
    ]:
        assert getattr(client, method)(url).status_code == 401, url
    assert client.post(JOBS, json={"dataset_id": some_id}).status_code == 401
