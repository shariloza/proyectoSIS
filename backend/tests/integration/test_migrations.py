"""La migración inicial crea el esquema aprobado y sus restricciones se cumplen en PostgreSQL."""

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Connection, Engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.shared.database import Base
from tests.integration.conftest import Migrate

pytestmark = pytest.mark.integration

EXPECTED_TABLES = {
    "admin_users",
    "datasets",
    "training_jobs",
    "model_versions",
    "model_activation_events",
    "predictions",
}


@pytest.fixture(scope="module", autouse=True)
def _schema(migrate: Migrate) -> None:
    migrate("upgrade", "head")


@pytest.fixture
def conn(engine: Engine) -> Iterator[Connection]:
    """Conexión cuya transacción se revierte al terminar cada test."""
    with engine.connect() as connection, connection.begin() as transaction:
        yield connection
        transaction.rollback()


def _insert(conn: Connection, table: str, **values: Any) -> uuid.UUID:
    columns = ", ".join(values)
    params = ", ".join(f":{key}" for key in values)
    row = conn.execute(
        text(f"INSERT INTO {table} ({columns}) VALUES ({params}) RETURNING id"), values
    )
    return uuid.UUID(str(row.scalar_one()))


def _dataset(conn: Connection) -> uuid.UUID:
    return _insert(
        conn,
        "datasets",
        original_filename="seed.csv",
        storage_path=f"datasets/{uuid.uuid4()}.csv",
        sha256="a" * 64,
        row_count=10,
        size_bytes=100,
        validation_report="{}",
    )


def _model(conn: Connection, dataset_id: uuid.UUID, status: str) -> uuid.UUID:
    return _insert(
        conn,
        "model_versions",
        version=f"v-{uuid.uuid4().hex[:8]}",
        dataset_id=dataset_id,
        algorithm="LogisticRegression",
        hyperparameters="{}",
        metrics="{}",
        acceptance_report="{}",
        dependencies="{}",
        preprocessing_version="1",
        random_seed=42,
        artifact_path=f"models/{uuid.uuid4()}.joblib",
        artifact_sha256="b" * 64,
        status=status,
        trained_at="2026-11-19T00:00:00Z",
    )


def test_creates_all_tables(engine: Engine) -> None:
    assert set(inspect(engine).get_table_names()) >= EXPECTED_TABLES


def test_migration_matches_orm_models(conn: Connection) -> None:
    diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)

    assert diff == []


def test_only_one_model_can_be_active(conn: Connection) -> None:
    dataset_id = _dataset(conn)
    _model(conn, dataset_id, "ACTIVE")

    with pytest.raises(IntegrityError, match="uq_model_versions_single_active"):
        _model(conn, dataset_id, "ACTIVE")


def test_rejects_unknown_model_status(conn: Connection) -> None:
    with pytest.raises(IntegrityError, match="ck_model_versions_status_allowed"):
        _model(conn, _dataset(conn), "DEPLOYED")


def test_rejects_probability_out_of_range(conn: Connection) -> None:
    model_id = _model(conn, _dataset(conn), "ACTIVE")

    with pytest.raises(IntegrityError, match="ck_predictions_probability_range"):
        _insert(
            conn,
            "predictions",
            model_version_id=model_id,
            input_features="{}",
            predicted_class=1,
            probability=1.5,
            risk_band="HIGH",
            latency_ms=3,
        )


def test_model_in_use_cannot_be_deleted(conn: Connection) -> None:
    dataset_id = _dataset(conn)
    _model(conn, dataset_id, "APPROVED")

    with pytest.raises(IntegrityError, match="fk_model_versions_dataset_id_datasets"):
        conn.execute(text("DELETE FROM datasets WHERE id = :id"), {"id": dataset_id})


def test_downgrade_and_upgrade_roundtrip(engine: Engine, migrate: Migrate) -> None:
    migrate("downgrade", "base")
    assert not EXPECTED_TABLES & set(inspect(engine).get_table_names())

    migrate("upgrade", "head")
    assert set(inspect(engine).get_table_names()) >= EXPECTED_TABLES
