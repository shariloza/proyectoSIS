"""Registra todos los modelos ORM en `Base.metadata`.

Todo punto de entrada (API, worker, bootstrap, Alembic) debe importar este módulo:
SQLAlchemy necesita conocer todas las tablas para resolver las claves foráneas.
"""

from app.modules.auth.infrastructure.records import AdminUserRecord
from app.modules.datasets.infrastructure.records import DatasetRecord
from app.modules.model_registry.infrastructure.records import (
    ModelActivationEventRecord,
    ModelVersionRecord,
)
from app.modules.prediction.infrastructure.records import PredictionRecord
from app.modules.training.infrastructure.records import TrainingJobRecord
from app.shared.database import Base

__all__ = [
    "AdminUserRecord",
    "Base",
    "DatasetRecord",
    "ModelActivationEventRecord",
    "ModelVersionRecord",
    "PredictionRecord",
    "TrainingJobRecord",
]
