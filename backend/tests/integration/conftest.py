from collections.abc import Callable

import pytest
from sqlalchemy import Engine

from tests.conftest import CreateDatabase, run_migrations

Migrate = Callable[[str, str], None]


@pytest.fixture(scope="session")
def engine(create_database: CreateDatabase) -> Engine:
    return create_database()


@pytest.fixture(scope="session")
def migrate(engine: Engine) -> Migrate:
    return lambda action, revision: run_migrations(engine, action, revision)
