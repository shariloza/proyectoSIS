"""Métricas de evaluación y criterios de aceptación (definidos en la Fase 1, antes de entrenar)."""

import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline

DECISION_THRESHOLD = 0.5
ROC_CURVE_POINTS = 50


@dataclass(frozen=True)
class Criterion:
    code: str
    description: str
    threshold: float
    higher_is_better: bool = True

    def passes(self, value: float) -> bool:
        return value >= self.threshold if self.higher_is_better else value <= self.threshold


ACCEPTANCE_CRITERIA = (
    Criterion("C1", "ROC-AUC en test", 0.85),
    Criterion("C2", "Recall de la clase 1 (riesgo)", 0.80),
    Criterion("C3", "Precisión de la clase 1", 0.75),
    Criterion("C4", "F1 macro", 0.78),
    Criterion("C5", "Mejora de ROC-AUC sobre el modelo Dummy", 0.25),
    Criterion("C6", "Brecha de recall entre géneros", 0.05, higher_is_better=False),
    Criterion("C7", "Brecha de ROC-AUC validación vs test", 0.03, higher_is_better=False),
    Criterion("C8", "Latencia p95 de una predicción (ms)", 100, higher_is_better=False),
)
# C9 (re-entrenamiento): el candidato no puede bajar el ROC-AUC del activo en más de esto.
MAX_AUC_REGRESSION = 0.01


def evaluate(model: Pipeline, features: pd.DataFrame, target: pd.Series) -> dict[str, Any]:
    probabilities = model.predict_proba(features)[:, 1]
    predictions = (probabilities >= DECISION_THRESHOLD).astype(int)
    report = classification_report(target, predictions, output_dict=True, zero_division=0)
    fpr, tpr, _ = roc_curve(target, probabilities)
    sample = np.linspace(0, len(fpr) - 1, min(ROC_CURVE_POINTS, len(fpr))).astype(int)

    return {
        "roc_auc": round(float(roc_auc_score(target, probabilities)), 4),
        "f1_macro": round(float(f1_score(target, predictions, average="macro")), 4),
        "accuracy": round(float(report["accuracy"]), 4),
        "per_class": {
            label: {
                "precision": round(report[label]["precision"], 4),
                "recall": round(report[label]["recall"], 4),
                "f1": round(report[label]["f1-score"], 4),
                "support": int(report[label]["support"]),
            }
            for label in ("0", "1")
        },
        "confusion_matrix": confusion_matrix(target, predictions, labels=[0, 1]).tolist(),
        "roc_curve": {
            "fpr": [round(float(v), 4) for v in fpr[sample]],
            "tpr": [round(float(v), 4) for v in tpr[sample]],
        },
        "recall_by_gender": {
            str(gender): round(
                float(recall_score(target[mask], predictions[mask.to_numpy()], zero_division=0)),
                4,
            )
            for gender, mask in ((g, features["gender"] == g) for g in ("Male", "Female"))
        },
        "threshold": DECISION_THRESHOLD,
    }


def latency_p95_ms(model: Pipeline, features: pd.DataFrame, samples: int = 200) -> float:
    rows = features.sample(n=min(samples, len(features)), random_state=0)
    timings = []
    for index in range(len(rows)):
        start = time.perf_counter()
        model.predict_proba(rows.iloc[[index]])
        timings.append((time.perf_counter() - start) * 1000)
    return round(float(np.percentile(timings, 95)), 3)


def check_acceptance(
    test_metrics: dict[str, Any],
    validation_auc: float,
    dummy_auc: float,
    latency_ms: float,
) -> dict[str, Any]:
    recall = test_metrics["recall_by_gender"]
    observed = {
        "C1": test_metrics["roc_auc"],
        "C2": test_metrics["per_class"]["1"]["recall"],
        "C3": test_metrics["per_class"]["1"]["precision"],
        "C4": test_metrics["f1_macro"],
        "C5": round(test_metrics["roc_auc"] - dummy_auc, 4),
        "C6": round(abs(recall["Male"] - recall["Female"]), 4),
        "C7": round(abs(validation_auc - test_metrics["roc_auc"]), 4),
        "C8": latency_ms,
    }
    results = [
        {
            "code": criterion.code,
            "description": criterion.description,
            "threshold": criterion.threshold,
            "operator": ">=" if criterion.higher_is_better else "<=",
            "value": observed[criterion.code],
            "passed": criterion.passes(observed[criterion.code]),
        }
        for criterion in ACCEPTANCE_CRITERIA
    ]
    return {"approved": all(r["passed"] for r in results), "criteria": results}


def no_regression(candidate_auc: float, active_auc: float) -> bool:
    """C9: un re-entrenamiento no puede empeorar al modelo activo más de lo tolerado."""
    return candidate_auc >= active_auc - MAX_AUC_REGRESSION


def with_regression_check(
    acceptance: dict[str, Any], candidate_auc: float, active_auc: float
) -> dict[str, Any]:
    """Agrega C9 al reporte de aceptación de un candidato de re-entrenamiento."""
    passed = no_regression(candidate_auc, active_auc)
    criterion = {
        "code": "C9",
        "description": f"No empeorar el ROC-AUC del modelo activo ({active_auc}) en más de",
        "threshold": MAX_AUC_REGRESSION,
        "operator": "<=",
        "value": round(active_auc - candidate_auc, 4),
        "passed": passed,
    }
    return {
        "approved": acceptance["approved"] and passed,
        "criteria": [*acceptance["criteria"], criterion],
    }
