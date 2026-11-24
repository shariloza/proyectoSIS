import numpy as np

from app.ml.dataset import PreparedDataset
from app.ml.features import build_preprocessor


def test_output_has_no_missing_values_even_with_nulls(prepared: PreparedDataset) -> None:
    features = prepared.features.copy()
    features.loc[features.index[:5], "financial_stress"] = np.nan

    transformed = build_preprocessor().fit_transform(features)

    assert not np.isnan(transformed).any()


def test_produces_the_expected_feature_set(prepared: PreparedDataset) -> None:
    preprocessor = build_preprocessor().fit(prepared.features)

    names = set(preprocessor.get_feature_names_out())

    assert {"age", "cgpa", "sleep_duration", "gender_Female", "family_history_Yes"} <= names
    assert {f"education_level_{level}" for level in ("secondary", "doctorate")} <= names
    assert not any("suicid" in name.lower() for name in names)


def test_unseen_education_level_does_not_break_inference(prepared: PreparedDataset) -> None:
    preprocessor = build_preprocessor().fit(prepared.features)
    row = prepared.features.head(1).assign(education_level="unknown")

    transformed = preprocessor.transform(row)

    assert transformed.shape[0] == 1


def test_scaling_is_learned_only_from_fit_data(prepared: PreparedDataset) -> None:
    half = len(prepared.features) // 2
    preprocessor = build_preprocessor().fit(prepared.features.iloc[:half])
    scaler = preprocessor.named_transformers_["numeric"].named_steps["scale"]

    expected = prepared.features.iloc[:half]["age"].mean()

    assert np.isclose(scaler.mean_[0], expected)
