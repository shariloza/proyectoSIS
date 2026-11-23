"""Base de datos temporal y aislada por sesión de tests, sobre el PostgreSQL real."""

import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from app.config import get_settings

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

Migrate = Callable[[str, str], None]


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    base_url = get_settings().database_url
    test_db = f"test_{uuid.uuid4().hex[:12]}"
    admin = create_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{test_db}"'))

    engine = create_engine(base_url.set(database=test_db))
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{test_db}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture(scope="session")
def migrate(engine: Engine) -> Migrate:
    """Ejecuta `alembic upgrade|downgrade <revision>` contra la base temporal."""

    def run(action: str, revision: str) -> None:
        with engine.begin() as connection:
            config = Config(str(ALEMBIC_INI))
            config.attributes["connection"] = connection
            getattr(command, action)(config, revision)

    return run
