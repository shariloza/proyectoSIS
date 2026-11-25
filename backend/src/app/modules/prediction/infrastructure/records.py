import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.prediction.domain.risk_band import RiskBand
from app.shared.database import Base, CreatedAtMixin, enum_check


class PredictionRecord(CreatedAtMixin, Base):
    """Historial de predicciones. Solo guarda las features del modelo, sin datos identificables."""

    __tablename__ = "predictions"
    __table_args__ = (
        enum_check("risk_band", RiskBand, "risk_band_allowed"),
        CheckConstraint("predicted_class IN (0, 1)", name="predicted_class_binary"),
        CheckConstraint("probability BETWEEN 0 AND 1", name="probability_range"),
        CheckConstraint("latency_milliseconds >= 0", name="latency_non_negative"),
        Index("ix_predictions_created_at", "created_at"),
        Index("ix_predictions_model_version_created_at", "model_version_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=func.gen_random_uuid()
    )
    model_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("model_versions.id", ondelete="RESTRICT")
    )
    input_features: Mapped[dict[str, Any]] = mapped_column(JSONB)
    predicted_class: Mapped[int] = mapped_column(SmallInteger)
    probability: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    risk_band: Mapped[str] = mapped_column(String(10))
    latency_milliseconds: Mapped[int] = mapped_column(Integer)
