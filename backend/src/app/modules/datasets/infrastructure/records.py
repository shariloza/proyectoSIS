import uuid
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base, CreatedAtMixin


class DatasetRecord(CreatedAtMixin, Base):
    """Archivo de entrenamiento versionado e inmutable, identificado por su hash."""

    __tablename__ = "datasets"
    __table_args__ = (
        CheckConstraint("row_count > 0", name="row_count_positive"),
        CheckConstraint("size_bytes > 0", name="size_bytes_positive"),
        CheckConstraint("char_length(sha256) = 64", name="sha256_length"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(512), unique=True)
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    row_count: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    validation_report: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # NULL solo para el dataset semilla cargado al instalar el sistema.
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="RESTRICT")
    )
