"""Validación y preparación del dataset de entrenamiento (CRISP-ML(Q): preparación de datos).

1. `validate_structure` falla rápido si el archivo no cumple el contrato (columnas,
   tipos, objetivo binario, tamaño mínimo).
2. `prepare` aplica el tratamiento documentado de cada hallazgo de calidad y
   descarta las filas fuera de dominio, dejando constancia en un reporte.
"""

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from app.ml.schema import (
    CATEGORICAL_FEATURES,
    EDUCATION_LEVEL_BY_DEGREE,
    EXCLUDED_COLUMNS,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    RAW_TO_CANONICAL,
    TARGET,
)

MIN_ROWS = 500
MAX_DROPPED_FRACTION = 0.05


class DatasetValidationError(ValueError):
    """El dataset no cumple el contrato. `problems` lista cada incumplimiento."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("Dataset inválido: " + "; ".join(problems))
        self.problems = problems


@dataclass(frozen=True)
class PreparationReport:
    raw_rows: int
    kept_rows: int
    dropped_by_reason: dict[str, int]
    imputed_nulls: dict[str, int]
    excluded_columns: list[str]
    class_balance: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class PreparedDataset:
    features: pd.DataFrame
    target: pd.Series
    report: PreparationReport


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(source: Path | BinaryIO) -> pd.DataFrame:
    try:
        return pd.read_csv(source)
    except (pd.errors.ParserError, UnicodeDecodeError, pd.errors.EmptyDataError) as exc:
        raise DatasetValidationError([f"el archivo no es un CSV legible ({exc})"]) from None


def validate_structure(raw: pd.DataFrame) -> None:
    problems: list[str] = []

    missing = sorted(set(RAW_TO_CANONICAL) - set(raw.columns))
    if missing:
        problems.append(f"faltan columnas: {', '.join(missing)}")
    if len(raw) < MIN_ROWS:
        problems.append(f"se requieren al menos {MIN_ROWS} filas (hay {len(raw)})")

    for feature in NUMERIC_FEATURES:
        raw_name = _raw_name(feature.name)
        if raw_name in raw.columns and not pd.api.types.is_numeric_dtype(raw[raw_name]):
            problems.append(f"la columna '{raw_name}' debe ser numérica")

    target_raw = _raw_name(TARGET)
    if target_raw in raw.columns:
        values = set(raw[target_raw].dropna().unique().tolist())
        if not values <= {0, 1}:
            problems.append(f"'{target_raw}' solo admite 0 y 1 (se encontró {sorted(values)})")
        if raw[target_raw].isna().any():
            problems.append(f"'{target_raw}' tiene valores vacíos")

    if problems:
        raise DatasetValidationError(problems)


def prepare(raw: pd.DataFrame) -> PreparedDataset:
    """Valida, limpia y devuelve las features canónicas y el objetivo."""
    validate_structure(raw)

    data = raw[list(RAW_TO_CANONICAL)].rename(columns=RAW_TO_CANONICAL)
    data["education_level"] = data.pop("degree").map(EDUCATION_LEVEL_BY_DEGREE)

    invalid_masks = {
        **{
            f"{feature.name} fuera de [{feature.minimum}, {feature.maximum}]": ~data[
                feature.name
            ].between(feature.minimum, feature.maximum)
            & data[feature.name].notna()
            for feature in NUMERIC_FEATURES
        },
        **{
            f"{name} con categoría no permitida": ~data[name].isin(allowed)
            for name, allowed in CATEGORICAL_FEATURES.items()
        },
    }
    dropped = pd.Series(False, index=data.index)
    dropped_by_reason: dict[str, int] = {}
    for reason, mask in invalid_masks.items():
        if count := int((mask & ~dropped).sum()):
            dropped_by_reason[reason] = count
        dropped |= mask

    if dropped.mean() > MAX_DROPPED_FRACTION:
        raise DatasetValidationError(
            [
                f"{dropped.mean():.1%} de filas fuera de dominio (máximo "
                f"{MAX_DROPPED_FRACTION:.0%}): {dropped_by_reason}"
            ]
        )

    clean = data[~dropped].reset_index(drop=True)
    # Los nulos numéricos se imputan dentro del Pipeline (sin leakage); aquí solo se reportan.
    nulls = clean[list(FEATURE_COLUMNS)].isna().sum()
    imputed = {str(name): int(count) for name, count in nulls.items() if count}
    target = clean.pop(TARGET).astype(int)

    report = PreparationReport(
        raw_rows=len(raw),
        kept_rows=len(clean),
        dropped_by_reason=dropped_by_reason,
        imputed_nulls=imputed,
        excluded_columns=sorted(set(raw.columns) & set(EXCLUDED_COLUMNS)),
        class_balance={
            str(label): round(float(share), 4)
            for label, share in target.value_counts(normalize=True).sort_index().items()
        },
    )
    return PreparedDataset(features=clean[list(FEATURE_COLUMNS)], target=target, report=report)


def _raw_name(canonical: str) -> str:
    return next(raw for raw, name in RAW_TO_CANONICAL.items() if name == canonical)
