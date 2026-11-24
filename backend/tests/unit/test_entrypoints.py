"""Regresión: el worker fallaba al arrancar porque no registraba la tabla admin_users."""

import subprocess
import sys

import pytest

CHECK = (
    "import {module}; "
    "from app.shared.database import Base, create_session_factory; "
    "create_session_factory('postgresql+psycopg://u:p@localhost/db'); "
    "from sqlalchemy.orm import configure_mappers; configure_mappers(); "
    "print(sorted(Base.metadata.tables))"
)


@pytest.mark.parametrize("module", ["app.worker", "app.bootstrap", "app.main"])
def test_entrypoint_registers_every_table(module: str) -> None:
    result = subprocess.run(  # noqa: S603 - comando fijo, sin entrada externa
        [sys.executable, "-c", CHECK.format(module=module)],
        capture_output=True,
        text=True,
        check=True,
    )

    for table in ("admin_users", "datasets", "training_jobs", "model_versions", "predictions"):
        assert table in result.stdout
