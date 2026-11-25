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

from app.machine_learning.evaluation import (
    check_acceptance,
    evaluate,
    latency_95th_percentile_milliseconds,
)
from app.machine_learning.features import build_preprocessor

RANDOM_SEED = 42
VALIDATION_SIZE = 0.15
TEST_SIZE = 0.15
CROSS_VALIDATION_FOLDS = 5
# Si dos modelos difieren en menos que esto (ROC-AUC de validación), se elige el más simple.
SIMPLICITY_TOLERANCE = 0.005
# Paralelismo acotado: cada proceso copia los datos; el worker tiene un límite de 2 GB.
PARALLEL_JOBS = 2


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
            RandomForestClassifier(n_estimators=300, n_jobs=1, random_state=seed),
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
    train_features: pd.DataFrame
    validation_features: pd.DataFrame
    test_features: pd.DataFrame
    train_target: pd.Series
    validation_target: pd.Series
    test_target: pd.Series


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
    """Divide en entrenamiento, validación y test (estratificado). El test se usa una sola vez."""
    remaining_features, test_features, remaining_target, test_target = train_test_split(
        features, target, test_size=TEST_SIZE, stratify=target, random_state=seed
    )
    train_features, validation_features, train_target, validation_target = train_test_split(
        remaining_features,
        remaining_target,
        test_size=VALIDATION_SIZE / (1 - TEST_SIZE),
        stratify=remaining_target,
        random_state=seed,
    )
    return Split(
        train_features,
        validation_features,
        test_features,
        train_target,
        validation_target,
        test_target,
    )


def train(
    features: pd.DataFrame,
    target: pd.Series,
    candidates: list[Candidate] | None = None,
    seed: int = RANDOM_SEED,
) -> TrainingResult:
    candidates = candidates or default_candidates(seed)
    split = split_dataset(features, target, seed)
    folds = StratifiedKFold(n_splits=CROSS_VALIDATION_FOLDS, shuffle=True, random_state=seed)

    fitted: list[tuple[Candidate, Pipeline, dict[str, Any]]] = []
    comparison: list[dict[str, Any]] = []
    for candidate in candidates:
        pipeline = Pipeline([("preprocess", build_preprocessor()), ("model", candidate.estimator)])
        search = GridSearchCV(
            pipeline,
            {f"model__{key}": values for key, values in candidate.grid.items()},
            scoring="roc_auc",
            cv=folds,
            n_jobs=PARALLEL_JOBS,
        )
        search.fit(split.train_features, split.train_target)
        model: Pipeline = search.best_estimator_
        candidate_metrics = evaluate(model, split.validation_features, split.validation_target)
        hyperparameters = {
            key.removeprefix("model__"): value for key, value in search.best_params_.items()
        }
        fitted.append((candidate, model, hyperparameters))
        comparison.append(
            {
                "algorithm": candidate.name,
                "best_hyperparameters": hyperparameters,
                "cross_validation_roc_auc": round(float(search.best_score_), 4),
                "validation_roc_auc": candidate_metrics["roc_auc"],
                "validation_f1_macro": candidate_metrics["f1_macro"],
                "validation_recall_risk_class": candidate_metrics["per_class"]["1"]["recall"],
            }
        )

    # El primer candidato es el modelo base (Dummy): solo sirve de referencia, nunca se elige.
    best_validation_roc_auc = max(row["validation_roc_auc"] for row in comparison[1:])
    chosen_index = next(
        index
        for index, row in enumerate(comparison)
        if index > 0 and row["validation_roc_auc"] >= best_validation_roc_auc - SIMPLICITY_TOLERANCE
    )
    candidate, model, hyperparameters = fitted[chosen_index]
    baseline_model = fitted[0][1]

    validation_metrics = evaluate(model, split.validation_features, split.validation_target)
    test_metrics = evaluate(model, split.test_features, split.test_target)
    baseline_metrics = evaluate(baseline_model, split.test_features, split.test_target)
    acceptance = check_acceptance(
        test_metrics,
        validation_roc_auc=validation_metrics["roc_auc"],
        baseline_roc_auc=baseline_metrics["roc_auc"],
        latency_milliseconds=latency_95th_percentile_milliseconds(model, split.test_features),
    )
    return TrainingResult(
        algorithm=candidate.name,
        model=model,
        hyperparameters=hyperparameters,
        comparison=comparison,
        validation_metrics=validation_metrics,
        test_metrics=test_metrics,
        acceptance=acceptance,
        split_sizes={
            "train": len(split.train_features),
            "validation": len(split.validation_features),
            "test": len(split.test_features),
        },
    )
