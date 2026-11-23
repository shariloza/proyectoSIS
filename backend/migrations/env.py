"""Entorno de Alembic.

La URL sale de la configuración validada de la app. Los tests pueden inyectar
una conexión propia en `config.attributes["connection"]`.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection, create_engine

from app.config import get_settings

# Importar los ORM registra sus tablas en Base.metadata.
from app.modules.auth.infrastructure import orm as _auth_orm  # noqa: F401
from app.modules.datasets.infrastructure import orm as _datasets_orm  # noqa: F401
from app.modules.model_registry.infrastructure import orm as _registry_orm  # noqa: F401
from app.modules.prediction.infrastructure import orm as _prediction_orm  # noqa: F401
from app.modules.training.infrastructure import orm as _training_orm  # noqa: F401
from app.shared.database import Base

config = context.config
if config.config_file_name is not None and not config.attributes.get("connection"):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _configure(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_offline() -> None:
    """Genera el SQL sin conectarse ni requerir .env (alembic upgrade head --sql)."""
    context.configure(
        url="postgresql+psycopg://",
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_online() -> None:
    injected: Connection | None = config.attributes.get("connection")
    if injected is not None:
        _configure(injected)
        return

    engine = create_engine(get_settings().database_url)
    with engine.connect() as connection:
        _configure(connection)
    engine.dispose()


if context.is_offline_mode():
    run_offline()
else:
    run_online()
