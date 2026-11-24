"""Inicialización idempotente: `python -m app.bootstrap --seed-dataset <csv>`.

1. Crea el administrador inicial (ADMIN_EMAIL / ADMIN_PASSWORD) si no existe.
2. Si no hay ningún modelo: registra el dataset semilla, entrena v1 y, si cumple los
   criterios de aceptación, lo activa. Si no los cumple, el sistema queda sin modelo
   activo (fail fast) y se informa por el log.
"""

import argparse
import logging
import uuid
from pathlib import Path

from sqlalchemy import select

from app.config import get_settings
from app.modules.auth.application.service import AuthService
from app.modules.auth.infrastructure.orm import AdminUserRecord
from app.modules.auth.infrastructure.security import PasswordHasher, TokenService
from app.modules.datasets.application.service import DatasetService
from app.modules.model_registry.application.service import ModelRegistryService
from app.modules.training.application.worker import train_and_save
from app.shared.database import create_session_factory
from app.shared.errors import ConflictError
from app.shared.logging import configure_logging

logger = logging.getLogger("app.bootstrap")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-dataset", type=Path, required=True)
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_level)
    sessions = create_session_factory(settings.database_url)
    tokens = TokenService(
        settings.jwt_secret.get_secret_value(),
        settings.jwt_issuer,
        settings.jwt_audience,
        settings.jwt_expire_minutes,
    )

    with sessions.begin() as session:
        auth = AuthService(session, PasswordHasher(), tokens)
        if auth.ensure_admin(settings.admin_email, settings.admin_password.get_secret_value()):
            logger.info("administrador inicial creado")

    with sessions.begin() as session:
        registry = ModelRegistryService(session)
        if registry.list():
            logger.info("ya existen modelos registrados; no se entrena el inicial")
            return

        datasets = DatasetService(
            session, settings.artifacts_dir, max_bytes=settings.max_upload_mb * 1024 * 1024
        )
        try:
            dataset = datasets.upload(
                args.seed_dataset.name, "text/csv", args.seed_dataset.read_bytes(), None
            )
        except ConflictError as exc:  # quedó registrado en un intento anterior
            dataset = datasets.get(uuid.UUID(exc.details["dataset_id"]))
        version = registry.next_version_name()
        logger.info("entrenando modelo inicial", extra={"version": version})
        metadata = train_and_save(
            settings.artifacts_dir / dataset.storage_path,
            settings.artifacts_dir / "models",
            version,
            active_auc=None,
        )
        model = registry.register(metadata, dataset_id=dataset.id, training_job_id=None)
        if not metadata["acceptance"]["approved"]:
            logger.error("el modelo inicial no cumple los criterios: no se activa")
            return

        admin = session.scalars(
            select(AdminUserRecord).where(AdminUserRecord.email == settings.admin_email.lower())
        ).one()
        registry.activate(model.id, performed_by=admin.id)
        logger.info("modelo inicial activado", extra={"version": version})


if __name__ == "__main__":
    main()
