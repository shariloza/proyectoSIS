"""App real contra su propia base PostgreSQL temporal, con un modelo pequeño ya activo."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression
from sqlalchemy import select

from app.api.dependencies import AppState
from app.config import Settings, get_settings
from app.main import build_state, create_app
from app.ml.artifact import save_model
from app.ml.dataset import prepare
from app.ml.training import Candidate, default_candidates, train
from app.modules.auth.application.service import AuthService
from app.modules.auth.infrastructure.orm import AdminUserRecord
from app.modules.datasets.application.service import DatasetService
from app.modules.model_registry.application.service import ModelRegistryService
from app.shared.rate_limit import RateLimiter
from tests.conftest import CreateDatabase, run_migrations
from tests.ml.conftest import DATASET_PATH

ADMIN_EMAIL = "admin@test.local"
ADMIN_PASSWORD = "test-admin-password"
SAMPLE_ROWS = 1500
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

VALID_PROFILE: dict[str, Any] = {
    "gender": "Female",
    "age": 21,
    "cgpa": 7.5,
    "academic_pressure": 4,
    "study_satisfaction": 2,
    "work_study_hours": 9,
    "financial_stress": 4,
    "sleep_duration": "5-6 hours",
    "dietary_habits": "Moderate",
    "education_level": "undergraduate",
    "family_history": "No",
}


@pytest.fixture(scope="session")
def sample_csv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("data") / "sample.csv"
    pd.read_csv(DATASET_PATH).sample(n=SAMPLE_ROWS, random_state=11).to_csv(path, index=False)
    return path


@pytest.fixture(scope="session")
def settings(create_database: CreateDatabase, tmp_path_factory: pytest.TempPathFactory) -> Settings:
    engine = create_database()
    run_migrations(engine, "upgrade", "head")
    return get_settings().model_copy(
        update={
            "postgres_db": engine.url.database,
            "artifacts_dir": tmp_path_factory.mktemp("artifacts"),
            "admin_email": ADMIN_EMAIL,
            "cors_origins": ["http://localhost:5173"],
        }
    )


@pytest.fixture(scope="session")
def state(settings: Settings, sample_csv: Path) -> AppState:
    state = build_state(settings)
    state.prediction_limiter = RateLimiter(max_requests=10_000, window_seconds=60)
    state.login_limiter = RateLimiter(max_requests=10_000, window_seconds=60)
    _seed(state, sample_csv)
    return state


def fast_candidates() -> list[Candidate]:
    return [
        default_candidates()[0],
        Candidate("LogisticRegression", LogisticRegression(max_iter=1000), {}),
    ]


def _seed(state: AppState, sample_csv: Path) -> None:
    """Admin + dataset semilla + modelo v1 activo."""
    with state.sessions.begin() as session:
        AuthService(session, state.hasher, state.tokens).ensure_admin(ADMIN_EMAIL, ADMIN_PASSWORD)
    with state.sessions.begin() as session:
        dataset = DatasetService(session, state.settings.artifacts_dir, MAX_UPLOAD_BYTES).upload(
            "seed.csv", "text/csv", sample_csv.read_bytes(), None
        )
        prepared = prepare(pd.read_csv(sample_csv))
        metadata = save_model(
            train(prepared.features, prepared.target, fast_candidates()),
            models_dir=state.settings.artifacts_dir / "models",
            version_name="v1",
            dataset_path=sample_csv,
            preparation=prepared.report,
        )
        registry = ModelRegistryService(session)
        model = registry.register(
            metadata | {"status": "APPROVED"}, dataset_id=dataset.id, training_job_id=None
        )
        admin = session.scalars(select(AdminUserRecord)).one()
        registry.activate(model.id, performed_by=admin.id)


@pytest.fixture(scope="session")
def client(state: AppState) -> Iterator[TestClient]:
    with TestClient(create_app(state)) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
