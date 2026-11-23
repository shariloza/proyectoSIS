"""Preprocesamiento como ColumnTransformer: viaja dentro del Pipeline y del artefacto."""

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

from app.ml.schema import (
    DIETARY_HABITS,
    EDUCATION_LEVELS,
    GENDER,
    NUMERIC_FEATURES,
    SLEEP_DURATION,
    YES_NO,
)


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    ordinal = Pipeline(
        [
            ("encode", OrdinalEncoder(categories=[list(SLEEP_DURATION), list(DIETARY_HABITS)])),
            ("scale", StandardScaler()),
        ]
    )
    binary = OneHotEncoder(categories=[list(GENDER), list(YES_NO)], drop="first")
    education = OneHotEncoder(categories=[list(EDUCATION_LEVELS)], handle_unknown="ignore")

    return ColumnTransformer(
        [
            ("numeric", numeric, [feature.name for feature in NUMERIC_FEATURES]),
            ("ordinal", ordinal, ["sleep_duration", "dietary_habits"]),
            ("binary", binary, ["gender", "family_history"]),
            ("education", education, ["education_level"]),
        ],
        verbose_feature_names_out=False,
    )
