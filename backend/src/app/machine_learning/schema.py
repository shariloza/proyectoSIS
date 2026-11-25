"""Contrato del dataset y de las features del modelo.

Es la única fuente de verdad sobre columnas, rangos y categorías. La usan la
preparación de datos, el entrenamiento y la validación de la API.
"""

from dataclasses import dataclass
from typing import Final

PREPROCESSING_VERSION: Final = "2"
TARGET: Final = "depression"


@dataclass(frozen=True)
class NumericFeature:
    name: str
    minimum: float
    maximum: float


# Columnas del CSV original -> nombre canónico usado en el sistema.
RAW_TO_CANONICAL: Final[dict[str, str]] = {
    "Gender": "gender",
    "Age": "age",
    "Academic Pressure": "academic_pressure",
    "CGPA": "grade_point_average",
    "Study Satisfaction": "study_satisfaction",
    "Sleep Duration": "sleep_duration",
    "Dietary Habits": "dietary_habits",
    "Degree": "degree",
    "Work/Study Hours": "work_study_hours",
    "Financial Stress": "financial_stress",
    "Family History of Mental Illness": "family_history",
    "Depression": TARGET,
}

# Columnas que existen en el CSV pero NO se usan (ver hallazgos en CLAUDE.md).
EXCLUDED_COLUMNS: Final[dict[str, str]] = {
    "Have you ever had suicidal thoughts ?": "dato extremadamente sensible; excluido por ética",
    "id": "identificador sin valor predictivo",
    "City": "alta cardinalidad con valores basura y riesgo de sesgo geográfico",
    "Profession": "99,9 % 'Student': varianza casi nula",
    "Work Pressure": "99,99 % en 0: varianza casi nula",
    "Job Satisfaction": "99,97 % en 0: varianza casi nula",
}

NUMERIC_FEATURES: Final = (
    NumericFeature("age", 18, 60),
    NumericFeature("grade_point_average", 0.01, 10),
    NumericFeature("academic_pressure", 1, 5),
    NumericFeature("study_satisfaction", 1, 5),
    NumericFeature("work_study_hours", 0, 12),
    NumericFeature("financial_stress", 1, 5),
)

# Categorías ordinales, de menor a mayor.
SLEEP_DURATION: Final = ("Less than 5 hours", "5-6 hours", "7-8 hours", "More than 8 hours")
DIETARY_HABITS: Final = ("Unhealthy", "Moderate", "Healthy")
GENDER: Final = ("Male", "Female")
YES_NO: Final = ("No", "Yes")

# El título se agrupa en nivel educativo: 28 valores con pocos casos generalizan peor.
EDUCATION_LEVEL_BY_DEGREE: Final[dict[str, str]] = {
    "Class 12": "secondary",
    **dict.fromkeys(
        [
            "B.Arch",
            "B.Com",
            "B.Ed",
            "B.Pharm",
            "B.Tech",
            "BA",
            "BBA",
            "BCA",
            "BE",
            "BHM",
            "BSc",
            "LLB",
            "MBBS",
        ],
        "undergraduate",
    ),
    **dict.fromkeys(
        ["LLM", "M.Com", "M.Ed", "M.Pharm", "M.Tech", "MA", "MBA", "MCA", "MD", "ME", "MHM", "MSc"],
        "postgraduate",
    ),
    "PhD": "doctorate",
    "Others": "other",
}
EDUCATION_LEVELS: Final = ("secondary", "undergraduate", "postgraduate", "doctorate", "other")

CATEGORICAL_FEATURES: Final[dict[str, tuple[str, ...]]] = {
    "gender": GENDER,
    "sleep_duration": SLEEP_DURATION,
    "dietary_habits": DIETARY_HABITS,
    "education_level": EDUCATION_LEVELS,
    "family_history": YES_NO,
}

FEATURE_COLUMNS: Final = (
    *(feature.name for feature in NUMERIC_FEATURES),
    *CATEGORICAL_FEATURES,
)
