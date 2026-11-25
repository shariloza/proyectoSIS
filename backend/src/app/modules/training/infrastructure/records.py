import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.training.domain.job_status import JobStatus
from app.shared.database import Base, CreatedAtMixin, enum_check

MAX_ATTEMPTS = 3


class TrainingJobRecord(CreatedAtMixin, Base):
    """Trabajo de re-entrenamiento. La tabla actúa como cola (SELECT ... SKIP LOCKED)."""

    __tablename__ = "training_jobs"
    __table_args__ = (
        enum_check("status", JobStatus, "status_allowed"),
        CheckConstraint(f"attempts BETWEEN 0 AND {MAX_ATTEMPTS}", name="attempts_range"),
        Index("ix_training_jobs_status_created_at", "status", "created_at"),
        # Como máximo un trabajo en ejecución a la vez.
        Index(
            "uq_training_jobs_single_running",
            text("(true)"),
            unique=True,
            postgresql_where=text(f"status = '{JobStatus.RUNNING}'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("datasets.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), server_default=JobStatus.PENDING)
    attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    error_message: Mapped[str | None] = mapped_column(Text)
    requested_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("admin_users.id", ondelete="RESTRICT")
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
