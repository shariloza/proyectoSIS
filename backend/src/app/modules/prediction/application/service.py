import time
import uuid
from decimal import Decimal
from typing import Any

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.machine_learning.evaluation import DECISION_THRESHOLD
from app.machine_learning.schema import FEATURE_COLUMNS
from app.modules.model_registry.application.active_model import ActiveModelProvider
from app.modules.model_registry.application.service import ModelRegistryService
from app.modules.model_registry.infrastructure.records import ModelVersionRecord
from app.modules.prediction.domain.risk_band import band_for
from app.modules.prediction.infrastructure.records import PredictionRecord
from app.shared.errors import ServiceUnavailableError


class PredictionService:
    def __init__(self, session: Session, models: ActiveModelProvider) -> None:
        self._session = session
        self._models = models

    def predict(self, features: dict[str, Any]) -> tuple[PredictionRecord, str]:
        """Predice con el modelo ACTIVO y guarda la predicción en el historial."""
        active = ModelRegistryService(self._session).get_active()
        if active is None:
            raise ServiceUnavailableError("No hay un modelo activo para predecir.")
        model = self._models.get(active)

        start = time.perf_counter()
        row = pd.DataFrame([features], columns=list(FEATURE_COLUMNS))
        probability = float(model.pipeline.predict_proba(row)[0, 1])
        latency_milliseconds = round((time.perf_counter() - start) * 1000)

        record = PredictionRecord(
            model_version_id=model.id,
            input_features=features,
            predicted_class=int(probability >= DECISION_THRESHOLD),
            probability=Decimal(f"{probability:.4f}"),
            risk_band=band_for(probability),
            latency_milliseconds=latency_milliseconds,
        )
        self._session.add(record)
        self._session.flush()
        self._session.refresh(record)
        return record, model.version

    def history(
        self, page: int, size: int, model_version_id: uuid.UUID | None
    ) -> tuple[list[tuple[PredictionRecord, str]], int]:
        query = select(PredictionRecord, ModelVersionRecord.version).join(
            ModelVersionRecord, PredictionRecord.model_version_id == ModelVersionRecord.id
        )
        if model_version_id is not None:
            query = query.where(PredictionRecord.model_version_id == model_version_id)

        total = self._session.scalar(select(func.count()).select_from(query.subquery())) or 0
        rows = self._session.execute(
            query.order_by(PredictionRecord.created_at.desc(), PredictionRecord.id)
            .offset((page - 1) * size)
            .limit(size)
        ).all()
        return [(record, version) for record, version in rows], total
