import pandas as pd
import pytest

from app.machine_learning.dataset import DatasetValidationError, prepare
from app.machine_learning.schema import FEATURE_COLUMNS

SUICIDAL = "Have you ever had suicidal thoughts ?"


def test_prepare_returns_only_contract_features(raw: pd.DataFrame) -> None:
    result = prepare(raw)

    assert tuple(result.features.columns) == FEATURE_COLUMNS
    assert len(result.features) == len(result.target)
    assert set(result.target.unique()) <= {0, 1}


def test_suicidal_thoughts_column_is_never_used(raw: pd.DataFrame) -> None:
    result = prepare(raw)

    assert SUICIDAL not in result.features.columns
    assert SUICIDAL in result.report.excluded_columns


def test_out_of_domain_rows_are_dropped_and_reported(raw: pd.DataFrame) -> None:
    dirty = raw.copy()
    dirty.loc[0, "Sleep Duration"] = "Others"
    dirty.loc[1, "CGPA"] = 0.0
    dirty.loc[2, "Academic Pressure"] = 0.0

    report = prepare(dirty).report

    assert report.raw_rows - report.kept_rows >= 3
    assert report.dropped_by_reason["sleep_duration con categoría no permitida"] >= 1
    assert report.dropped_by_reason["grade_point_average fuera de [0.01, 10]"] >= 1


def test_degree_is_grouped_into_education_level(raw: pd.DataFrame) -> None:
    sample = raw.copy()
    sample.loc[0, "Degree"] = "PhD"
    sample.loc[1, "Degree"] = "Class 12"

    levels = prepare(sample).features["education_level"]

    assert levels.iloc[0] == "doctorate"
    assert levels.iloc[1] == "secondary"


def test_missing_columns_fail_fast(raw: pd.DataFrame) -> None:
    with pytest.raises(DatasetValidationError, match="faltan columnas: CGPA"):
        prepare(raw.drop(columns=["CGPA"]))


def test_non_binary_target_fails(raw: pd.DataFrame) -> None:
    broken = raw.copy()
    broken.loc[0, "Depression"] = 2

    with pytest.raises(DatasetValidationError, match="solo admite 0 y 1"):
        prepare(broken)


def test_non_numeric_column_fails(raw: pd.DataFrame) -> None:
    broken = raw.astype({"Age": str})
    broken.loc[0, "Age"] = "veinte"

    with pytest.raises(DatasetValidationError, match="'Age' debe ser numérica"):
        prepare(broken)


def test_too_few_rows_fails(raw: pd.DataFrame) -> None:
    with pytest.raises(DatasetValidationError, match="al menos 500 filas"):
        prepare(raw.head(100))


def test_too_dirty_dataset_is_rejected(raw: pd.DataFrame) -> None:
    dirty = raw.copy()
    dirty.loc[: len(dirty) // 10, "Dietary Habits"] = "Others"

    with pytest.raises(DatasetValidationError, match="fuera de dominio"):
        prepare(dirty)


def test_all_problems_are_reported_together(raw: pd.DataFrame) -> None:
    with pytest.raises(DatasetValidationError) as error:
        prepare(raw.drop(columns=["CGPA"]).head(10))

    assert len(error.value.problems) == 2
