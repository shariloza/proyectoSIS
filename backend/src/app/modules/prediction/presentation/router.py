import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, WithJsonSchema

from app.api.dependencies import Admin, limit_predictions, prediction_service
from app.api.errors import documented_errors
from app.machine_learning.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from app.modules.prediction.application.service import PredictionService
from app.modules.prediction.domain.risk_band import DISCLAIMER, RiskBand

router = APIRouter(prefix="/predictions", tags=["Predicciones"])

_RANGE = {feature.name: feature for feature in NUMERIC_FEATURES}


def _numeric(name: str, description: str) -> Any:
    feature = _RANGE[name]
    return Field(ge=feature.minimum, le=feature.maximum, description=description)


class _OneOf:
    """Restringe un str a las categorías del contrato (schema.py) y las publica como enum."""

    def __init__(self, feature: str) -> None:
        self.allowed = CATEGORICAL_FEATURES[feature]
        self.validator = AfterValidator(self._check)
        self.schema = WithJsonSchema({"type": "string", "enum": list(self.allowed)})

    def _check(self, value: str) -> str:
        if value not in self.allowed:
            raise ValueError(f"valor no permitido; opciones: {', '.join(self.allowed)}")
        return value


_gender, _sleep_duration, _dietary_habits, _education_level, _family_history = (
    _OneOf(name)
    for name in ("gender", "sleep_duration", "dietary_habits", "education_level", "family_history")
)
Gender = Annotated[str, _gender.validator, _gender.schema]
SleepDuration = Annotated[str, _sleep_duration.validator, _sleep_duration.schema]
DietaryHabits = Annotated[str, _dietary_habits.validator, _dietary_habits.schema]
EducationLevel = Annotated[str, _education_level.validator, _education_level.schema]
YesNo = Annotated[str, _family_history.validator, _family_history.schema]


class StudentProfileIn(BaseModel):
    """Respuestas del formulario. No incluye datos identificables."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "gender": "Female",
                    "age": 21,
                    "grade_point_average": 7.5,
                    "academic_pressure": 4,
                    "study_satisfaction": 2,
                    "work_study_hours": 9,
                    "financial_stress": 4,
                    "sleep_duration": "5-6 hours",
                    "dietary_habits": "Moderate",
                    "education_level": "undergraduate",
                    "family_history": "No",
                }
            ]
        },
    )

    gender: Gender = Field(description="Género")
    age: int = _numeric("age", "Edad en años")
    grade_point_average: float = _numeric("grade_point_average", "Promedio académico (escala 0-10)")
    academic_pressure: int = _numeric("academic_pressure", "Presión académica percibida (1-5)")
    study_satisfaction: int = _numeric("study_satisfaction", "Satisfacción con los estudios (1-5)")
    work_study_hours: int = _numeric("work_study_hours", "Horas diarias de estudio/trabajo")
    financial_stress: int = _numeric("financial_stress", "Estrés financiero percibido (1-5)")
    sleep_duration: SleepDuration = Field(description="Horas de sueño por noche")
    dietary_habits: DietaryHabits = Field(description="Hábitos alimenticios")
    education_level: EducationLevel = Field(description="Nivel educativo en curso")
    family_history: YesNo = Field(description="Antecedentes familiares de enfermedad mental")


class PredictionOut(BaseModel):
    id: uuid.UUID
    prediction: int = Field(description="1 = riesgo de depresión, 0 = sin riesgo")
    probability: float = Field(description="Probabilidad estimada de la clase 1")
    risk_band: RiskBand = Field(description="LOW < 0,40 ≤ MODERATE < 0,70 ≤ HIGH")
    model_version: str
    disclaimer: str = Field(examples=[DISCLAIMER])
    created_at: datetime


class PredictionHistoryItem(BaseModel):
    id: uuid.UUID
    input: dict[str, Any]
    prediction: int
    probability: float
    risk_band: RiskBand
    model_version: str
    model_version_id: uuid.UUID
    created_at: datetime


class PredictionPage(BaseModel):
    items: list[PredictionHistoryItem]
    total: int
    page: int
    size: int


Service = Annotated[PredictionService, Depends(prediction_service)]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Estimar el riesgo de depresión",
    description=(
        "Usa únicamente el modelo ACTIVO. Guarda en el historial la entrada, el resultado, "
        "la probabilidad, la versión del modelo y la fecha. Límite: 30 solicitudes/min por IP."
    ),
    response_model=PredictionOut,
    responses=documented_errors(422, 429, 503),
    dependencies=[Depends(limit_predictions)],
)
def predict(body: StudentProfileIn, service: Service) -> PredictionOut:
    record, version = service.predict(body.model_dump())
    return PredictionOut(
        id=record.id,
        prediction=record.predicted_class,
        probability=float(record.probability),
        risk_band=RiskBand(record.risk_band),
        model_version=version,
        disclaimer=DISCLAIMER,
        created_at=record.created_at,
    )


@router.get(
    "",
    summary="Historial de predicciones (admin)",
    description=(
        "Paginado, del más reciente al más antiguo. Restringido: son datos de salud mental."
    ),
    response_model=PredictionPage,
    responses=documented_errors(401, 403, 422),
)
def history(
    _: Admin,
    service: Service,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    model_version_id: uuid.UUID | None = None,
) -> PredictionPage:
    rows, total = service.history(page, size, model_version_id)
    return PredictionPage(
        items=[
            PredictionHistoryItem(
                id=record.id,
                input=record.input_features,
                prediction=record.predicted_class,
                probability=float(record.probability),
                risk_band=RiskBand(record.risk_band),
                model_version=version,
                model_version_id=record.model_version_id,
                created_at=record.created_at,
            )
            for record, version in rows
        ],
        total=total,
        page=page,
        size=size,
    )
