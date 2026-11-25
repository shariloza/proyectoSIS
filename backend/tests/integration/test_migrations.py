"""Las migraciones crean el esquema aprobado y sus restricciones se cumplen en PostgreSQL."""

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
def connection(engine: Engine) -> Iterator[Connection]:
    """Conexión cuya transacción se revierte al terminar cada test."""
    with engine.connect() as connection, connection.begin() as transaction:
        yield connection
        transaction.rollback()


def _insert(connection: Connection, table: str, **values: Any) -> uuid.UUID:
    columns = ", ".join(values)
    placeholders = ", ".join(f":{key}" for key in values)
    row = connection.execute(
        text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"), values
    )
    return uuid.UUID(str(row.scalar_one()))


def _dataset(connection: Connection) -> uuid.UUID:
    return _insert(
        connection,
        "datasets",
        original_filename="seed.csv",
        storage_path=f"datasets/{uuid.uuid4()}.csv",
        sha256="a" * 64,
        row_count=10,
        size_bytes=100,
        validation_report="{}",
    )


def _model(connection: Connection, dataset_id: uuid.UUID, status: str) -> uuid.UUID:
    return _insert(
        connection,
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


def test_migration_matches_records(connection: Connection) -> None:
    diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert diff == []


def test_only_one_model_can_be_active(connection: Connection) -> None:
    dataset_id = _dataset(connection)
    _model(connection, dataset_id, "ACTIVE")

    with pytest.raises(IntegrityError, match="uq_model_versions_single_active"):
        _model(connection, dataset_id, "ACTIVE")


def test_rejects_unknown_model_status(connection: Connection) -> None:
    with pytest.raises(IntegrityError, match="ck_model_versions_status_allowed"):
        _model(connection, _dataset(connection), "DEPLOYED")


def test_rejects_probability_out_of_range(connection: Connection) -> None:
    model_id = _model(connection, _dataset(connection), "ACTIVE")

    with pytest.raises(IntegrityError, match="ck_predictions_probability_range"):
        _insert(
            connection,
            "predictions",
            model_version_id=model_id,
            input_features="{}",
            predicted_class=1,
            probability=1.5,
            risk_band="HIGH",
            latency_milliseconds=3,
        )


def test_model_in_use_cannot_be_deleted(connection: Connection) -> None:
    dataset_id = _dataset(connection)
    _model(connection, dataset_id, "APPROVED")

    with pytest.raises(IntegrityError, match="fk_model_versions_dataset_id_datasets"):
        connection.execute(text("DELETE FROM datasets WHERE id = :id"), {"id": dataset_id})


def test_downgrade_and_upgrade_roundtrip(engine: Engine, migrate: Migrate) -> None:
    migrate("downgrade", "base")
    assert not EXPECTED_TABLES & set(inspect(engine).get_table_names())

    migrate("upgrade", "head")
    assert set(inspect(engine).get_table_names()) >= EXPECTED_TABLES


def test_clear_names_migration_keeps_saved_predictions(engine: Engine, migrate: Migrate) -> None:
    """0002 renombra latency_ms y la clave cgpa sin perder el historial existente."""
    migrate("downgrade", "0001")
    with engine.begin() as connection:
        model_id = _model(connection, _dataset(connection), "ACTIVE")
        _insert(
            connection,
            "predictions",
            model_version_id=model_id,
            input_features='{"cgpa": 7.5, "age": 21}',
            predicted_class=1,
            probability=0.8,
            risk_band="HIGH",
            latency_ms=4,
        )

    migrate("upgrade", "head")

    with engine.begin() as connection:
        saved = connection.execute(
            text("SELECT input_features, latency_milliseconds FROM predictions")
        ).one()
        connection.execute(text("DELETE FROM predictions"))
        connection.execute(text("DELETE FROM model_versions"))
        connection.execute(text("DELETE FROM datasets"))
    assert saved.input_features == {"grade_point_average": 7.5, "age": 21}
    assert saved.latency_milliseconds == 4
