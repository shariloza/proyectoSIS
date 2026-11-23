import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.model_registry.domain.status import ActivationAction, ModelStatus
from app.shared.database import Base, CreatedAtMixin, enum_check


class ModelVersionRecord(Base):
    """Versión inmutable de un modelo entrenado (sección 6.2 de la base)."""

    __tablename__ = "model_versions"
    __table_args__ = (
        enum_check("status", ModelStatus, "status_allowed"),
        CheckConstraint("char_length(artifact_sha256) = 64", name="artifact_sha256_length"),
        # Exactamente un modelo activo como máximo.
        Index(
            "uq_model_versions_single_active",
            text("(true)"),
            unique=True,
            postgresql_where=text(f"status = '{ModelStatus.ACTIVE}'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    version: Mapped[str] = mapped_column(String(20), unique=True)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="RESTRICT"), index=True
    )
    # NULL solo para el modelo inicial entrenado al instalar el sistema.
    training_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("training_jobs.id", ondelete="RESTRICT"), unique=True
    )
    algorithm: Mapped[str] = mapped_column(String(100))
    hyperparameters: Mapped[dict[str, Any]] = mapped_column(JSONB)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB)
    acceptance_report: Mapped[dict[str, Any]] = mapped_column(JSONB)
    dependencies: Mapped[dict[str, str]] = mapped_column(JSONB)
    preprocessing_version: Mapped[str] = mapped_column(String(20))
    random_seed: Mapped[int] = mapped_column(Integer)
    artifact_path: Mapped[str] = mapped_column(String(512), unique=True)
    artifact_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), index=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ModelActivationEventRecord(CreatedAtMixin, Base):
    """Auditoría de activaciones y rollbacks. Permite reconstruir qué modelo estuvo activo."""

    __tablename__ = "model_activation_events"
    __table_args__ = (enum_check("action", ActivationAction, "action_allowed"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT"), index=True
    )
    previous_model_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT")
    )
    action: Mapped[str] = mapped_column(String(20))
    performed_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("admin_users.id", ondelete="RESTRICT")
    )
