"""Bases de datos temporales y aisladas sobre el PostgreSQL real (una por suite)."""

import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from app.config import get_settings

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"

CreateDatabase = Callable[[], Engine]


@pytest.fixture(scope="session")
def create_database() -> Iterator[CreateDatabase]:
    base_url = get_settings().database_url
    admin = create_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    created: list[tuple[str, Engine]] = []

    def create() -> Engine:
        name = f"test_{uuid.uuid4().hex[:12]}"
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
        engine = create_engine(base_url.set(database=name))
        created.append((name, engine))
        return engine

    yield create

    for name, engine in created:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    admin.dispose()


def run_migrations(engine: Engine, action: str, revision: str) -> None:
    """Ejecuta `alembic upgrade|downgrade <revision>` contra la base indicada."""
    with engine.begin() as connection:
        config = Config(str(ALEMBIC_INI))
        config.attributes["connection"] = connection
        getattr(command, action)(config, revision)
