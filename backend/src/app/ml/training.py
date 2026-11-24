"""Entrenamiento, comparación y selección de modelos (CRISP-ML(Q): ingeniería del modelo)."""

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

from app.ml.evaluation import check_acceptance, evaluate, latency_p95_ms
from app.ml.features import build_preprocessor

RANDOM_SEED = 42
VALIDATION_SIZE = 0.15
TEST_SIZE = 0.15
CV_FOLDS = 5
# Si dos modelos difieren en menos que esto (ROC-AUC de validación), se elige el más simple.
SIMPLICITY_TOLERANCE = 0.005


@dataclass(frozen=True)
class Candidate:
    """Algoritmo a comparar. El orden en CANDIDATES va de más simple a más complejo."""

    name: str
    estimator: ClassifierMixin
    grid: dict[str, list[Any]]


def default_candidates(seed: int = RANDOM_SEED) -> list[Candidate]:
    return [
        Candidate("DummyClassifier", DummyClassifier(strategy="prior"), {}),
        Candidate(
            "LogisticRegression",
            LogisticRegression(max_iter=2000, random_state=seed),
            {"C": [0.1, 1.0, 10.0]},
        ),
        Candidate(
            "RandomForestClassifier",
            RandomForestClassifier(n_estimators=300, n_jobs=-1, random_state=seed),
            {"max_depth": [8, 16], "min_samples_leaf": [5, 20]},
        ),
        Candidate(
            "HistGradientBoostingClassifier",
            HistGradientBoostingClassifier(random_state=seed),
            {"learning_rate": [0.05, 0.1], "max_leaf_nodes": [15, 31]},
        ),
    ]


@dataclass(frozen=True)
class Split:
    x_train: pd.DataFrame
    x_val: pd.DataFrame
    x_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series


@dataclass(frozen=True)
class TrainingResult:
    algorithm: str
    model: Pipeline
    hyperparameters: dict[str, Any]
    comparison: list[dict[str, Any]]
    validation_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    acceptance: dict[str, Any]
    split_sizes: dict[str, int]


def split_dataset(features: pd.DataFrame, target: pd.Series, seed: int = RANDOM_SEED) -> Split:
    """Train/val/test estratificado. El test solo se usa una vez, al final."""
    x_rest, x_test, y_rest, y_test = train_test_split(
        features, target, test_size=TEST_SIZE, stratify=target, random_state=seed
    )
    x_train, x_val, y_train, y_val = train_test_split(
        x_rest,
        y_rest,
        test_size=VALIDATION_SIZE / (1 - TEST_SIZE),
        stratify=y_rest,
        random_state=seed,
    )
    return Split(x_train, x_val, x_test, y_train, y_val, y_test)


def train(
    features: pd.DataFrame,
    target: pd.Series,
    candidates: list[Candidate] | None = None,
    seed: int = RANDOM_SEED,
) -> TrainingResult:
    candidates = candidates or default_candidates(seed)
    split = split_dataset(features, target, seed)
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=seed)

    fitted: list[tuple[Candidate, Pipeline, dict[str, Any]]] = []
    comparison: list[dict[str, Any]] = []
    for candidate in candidates:
        pipeline = Pipeline([("preprocess", build_preprocessor()), ("model", candidate.estimator)])
        search = GridSearchCV(
            pipeline,
            {f"model__{key}": values for key, values in candidate.grid.items()},
            scoring="roc_auc",
            cv=cv,
            n_jobs=-1,
        )
        search.fit(split.x_train, split.y_train)
        model: Pipeline = search.best_estimator_
        val_metrics = evaluate(model, split.x_val, split.y_val)
        params = {key.removeprefix("model__"): value for key, value in search.best_params_.items()}
        fitted.append((candidate, model, params))
        comparison.append(
            {
                "algorithm": candidate.name,
                "best_params": params,
                "cv_roc_auc": round(float(search.best_score_), 4),
                "val_roc_auc": val_metrics["roc_auc"],
                "val_f1_macro": val_metrics["f1_macro"],
                "val_recall_1": val_metrics["per_class"]["1"]["recall"],
            }
        )

    best_auc = max(row["val_roc_auc"] for row in comparison[1:])
    chosen_index = next(
        index
        for index, row in enumerate(comparison)
        if index > 0 and row["val_roc_auc"] >= best_auc - SIMPLICITY_TOLERANCE
    )
    candidate, model, params = fitted[chosen_index]
    dummy_model = fitted[0][1]

    validation_metrics = evaluate(model, split.x_val, split.y_val)
    test_metrics = evaluate(model, split.x_test, split.y_test)
    acceptance = check_acceptance(
        test_metrics,
        validation_auc=validation_metrics["roc_auc"],
        dummy_auc=evaluate(dummy_model, split.x_test, split.y_test)["roc_auc"],
        latency_ms=latency_p95_ms(model, split.x_test),
    )
    return TrainingResult(
        algorithm=candidate.name,
        model=model,
        hyperparameters=params,
        comparison=comparison,
        validation_metrics=validation_metrics,
        test_metrics=test_metrics,
        acceptance=acceptance,
        split_sizes={
            "train": len(split.x_train),
            "val": len(split.x_val),
            "test": len(split.x_test),
        },
    )
