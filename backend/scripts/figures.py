"""EDA reproducible y gráficas del modelo para el documento final.

Uso (desde backend/):
    uv run python scripts/figures.py --dataset ../data/raw/student_depression_dataset.csv \
        --metadata ../artifacts/models/v1/metadata.json --output ../docs/figuras
"""

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from app.machine_learning.dataset import prepare, read_csv

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
NO_RISK = "#2a78d6"  # clase 0
RISK = "#eb6834"  # clase 1
SEQUENTIAL = LinearSegmentedColormap.from_list("blue", ["#f0efec", "#86b6ef", "#1c5cab"])
DIVERGING = LinearSegmentedColormap.from_list("div", [RISK, "#f0efec", NO_RISK])
CLASS_LABELS = {0: "Sin depresión", 1: "Con depresión"}

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK_SECONDARY,
        "axes.titlecolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": INK_SECONDARY,
        "ytick.color": INK_SECONDARY,
        "font.size": 10,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
    }
)


def target_distribution(data: pd.DataFrame, output_directory: Path) -> None:
    counts = data["depression"].value_counts().sort_index()
    figure, axis = plt.subplots(figsize=(6, 4))
    bars = axis.bar(
        [CLASS_LABELS[label] for label in counts.index],
        counts.values,
        color=[NO_RISK, RISK],
        width=0.55,
    )
    for bar, value in zip(bars, counts.values, strict=True):
        axis.annotate(
            f"{value:,} ({value / counts.sum():.1%})".replace(",", "."),
            (bar.get_x() + bar.get_width() / 2, value),
            ha="center",
            va="bottom",
            color=INK,
            xytext=(0, 4),
            textcoords="offset points",
        )
    axis.set_title("Distribución de la variable objetivo")
    axis.set_ylabel("Estudiantes")
    axis.grid(axis="x", visible=False)
    _save(figure, output_directory / "01_distribucion_objetivo.png")


def risk_factors(data: pd.DataFrame, output_directory: Path) -> None:
    panels = [
        ("academic_pressure", "Presión académica (1-5)", None),
        ("financial_stress", "Estrés financiero (1-5)", None),
        (
            "sleep_duration",
            "Horas de sueño",
            ["Less than 5 hours", "5-6 hours", "7-8 hours", "More than 8 hours"],
        ),
        ("dietary_habits", "Hábitos alimenticios", ["Unhealthy", "Moderate", "Healthy"]),
    ]
    labels_es = {
        "Less than 5 hours": "<5 h",
        "5-6 hours": "5-6 h",
        "7-8 hours": "7-8 h",
        "More than 8 hours": ">8 h",
        "Unhealthy": "No saludable",
        "Moderate": "Moderado",
        "Healthy": "Saludable",
    }
    figure, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    for axis, (column, title, order) in zip(axes.flat, panels, strict=True):
        rate = data.groupby(column)["depression"].mean()
        if order:
            rate = rate.reindex(order)
        names = [
            labels_es.get(str(k), str(int(k)) if isinstance(k, float) else k) for k in rate.index
        ]
        axis.bar(names, rate.values * 100, color=RISK, width=0.6)
        axis.set_title(title)
        axis.set_ylim(0, 100)
        axis.grid(axis="x", visible=False)
    for axis in axes[:, 0]:
        axis.set_ylabel("% con depresión")
    figure.suptitle("Tasa de depresión según factores de riesgo", fontweight="bold", color=INK)
    figure.tight_layout()
    _save(figure, output_directory / "02_factores_de_riesgo.png")


def correlations(data: pd.DataFrame, output_directory: Path) -> None:
    numeric = data.select_dtypes("number")
    names = {
        "age": "Edad",
        "grade_point_average": "Promedio (CGPA)",
        "academic_pressure": "Presión académica",
        "study_satisfaction": "Satisfacción estudio",
        "work_study_hours": "Horas estudio/trabajo",
        "financial_stress": "Estrés financiero",
        "depression": "Depresión",
    }
    correlation = numeric.rename(columns=names).corr()
    figure, axis = plt.subplots(figsize=(7.5, 6))
    image = axis.imshow(correlation.values, cmap=DIVERGING, vmin=-1, vmax=1)
    axis.set_xticks(range(len(correlation)), correlation.columns, rotation=40, ha="right")
    axis.set_yticks(range(len(correlation)), correlation.columns)
    axis.grid(visible=False)
    for row in range(len(correlation)):
        for column in range(len(correlation)):
            axis.text(
                column,
                row,
                f"{correlation.iloc[row, column]:.2f}",
                ha="center",
                va="center",
                color=INK,
                fontsize=8,
            )
    figure.colorbar(image, ax=axis, shrink=0.8, label="Correlación de Pearson")
    axis.set_title("Correlación entre variables numéricas")
    _save(figure, output_directory / "03_correlaciones.png")


def model_comparison(metadata: dict[str, Any], output_directory: Path) -> None:
    rows = metadata["comparison"]
    names = [row["algorithm"].replace("Classifier", "") for row in rows]
    metrics = [
        ("cross_validation_roc_auc", "ROC-AUC (CV 5 pliegues)", NO_RISK),
        ("validation_roc_auc", "ROC-AUC validación", RISK),
    ]
    figure, axis = plt.subplots(figsize=(8, 4.5))
    width = 0.36
    for offset, (key, label, color) in enumerate(metrics):
        positions = [index + (offset - 0.5) * (width + 0.02) for index in range(len(rows))]
        bars = axis.bar(
            positions, [row[key] for row in rows], width=width, color=color, label=label
        )
        axis.bar_label(bars, fmt="%.3f", fontsize=8, color=INK, padding=2)
    axis.axhline(0.85, color=INK_SECONDARY, linestyle="--", linewidth=1)
    axis.text(-0.4, 0.86, "criterio C1 = 0,85", color=INK_SECONDARY, ha="left", fontsize=8)
    axis.set_xticks(range(len(rows)), names)
    axis.set_ylim(0.4, 1.0)
    axis.set_ylabel("ROC-AUC")
    axis.set_title(f"Comparación de modelos (elegido: {metadata['algorithm']})")
    axis.legend(frameon=False, loc="upper left")
    axis.grid(axis="x", visible=False)
    _save(figure, output_directory / "04_comparacion_modelos.png")


def confusion(metadata: dict[str, Any], output_directory: Path) -> None:
    matrix = metadata["metrics"]["test"]["confusion_matrix"]
    figure, axis = plt.subplots(figsize=(5.5, 4.8))
    axis.imshow(matrix, cmap=SEQUENTIAL)
    labels = list(CLASS_LABELS.values())
    axis.set_xticks([0, 1], labels)
    axis.set_yticks([0, 1], labels)
    axis.set_xlabel("Predicción")
    axis.set_ylabel("Valor real")
    axis.grid(visible=False)
    total = sum(map(sum, matrix))
    darkest = max(map(max, matrix))
    for actual in range(2):
        for predicted in range(2):
            count = matrix[actual][predicted]
            axis.text(
                predicted,
                actual,
                f"{count:,}\n{count / total:.1%}".replace(",", "."),
                ha="center",
                va="center",
                color=SURFACE if count > darkest * 0.7 else INK,
                fontsize=11,
                fontweight="bold",
            )
    axis.set_title(f"Matriz de confusión — test ({metadata['version']})")
    _save(figure, output_directory / "05_matriz_confusion.png")


def roc(metadata: dict[str, Any], output_directory: Path) -> None:
    curve = metadata["metrics"]["test"]["roc_curve"]
    auc = metadata["metrics"]["test"]["roc_auc"]
    figure, axis = plt.subplots(figsize=(5.5, 5))
    axis.plot(
        curve["false_positive_rate"],
        curve["true_positive_rate"],
        color=NO_RISK,
        linewidth=2,
        label=f"{metadata['algorithm']} (AUC = {auc:.3f})",
    )
    axis.plot(
        [0, 1], [0, 1], color=INK_SECONDARY, linestyle="--", linewidth=1, label="Azar (AUC = 0,5)"
    )
    axis.set_xlabel("Tasa de falsos positivos")
    axis.set_ylabel("Tasa de verdaderos positivos (recall)")
    axis.set_title("Curva ROC — conjunto de test")
    axis.legend(frameon=False, loc="lower right")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1.01)
    _save(figure, output_directory / "06_curva_roc.png")


def class_metrics(metadata: dict[str, Any], output_directory: Path) -> None:
    per_class = metadata["metrics"]["test"]["per_class"]
    metrics = [("precision", "Precisión"), ("recall", "Recall"), ("f1", "F1")]
    figure, axis = plt.subplots(figsize=(7, 4))
    width = 0.36
    for offset, (label, color) in enumerate(((0, NO_RISK), (1, RISK))):
        positions = [index + (offset - 0.5) * (width + 0.02) for index in range(len(metrics))]
        values = [per_class[str(label)][key] for key, _ in metrics]
        bars = axis.bar(positions, values, width=width, color=color, label=CLASS_LABELS[label])
        axis.bar_label(bars, fmt="%.3f", fontsize=8, color=INK, padding=2)
    axis.set_xticks(range(len(metrics)), [name for _, name in metrics])
    axis.set_ylim(0, 1)
    axis.set_title("Métricas por clase — conjunto de test")
    axis.legend(frameon=False, loc="lower right")
    axis.grid(axis="x", visible=False)
    _save(figure, output_directory / "07_metricas_por_clase.png")


def _save(figure: plt.Figure, path: Path) -> None:
    figure.savefig(path)
    plt.close(figure)
    print(f"generada {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)

    prepared = prepare(read_csv(arguments.dataset))
    data = prepared.features.assign(depression=prepared.target)
    metadata = json.loads(arguments.metadata.read_text(encoding="utf-8"))

    target_distribution(data, arguments.output)
    risk_factors(data, arguments.output)
    correlations(data, arguments.output)
    model_comparison(metadata, arguments.output)
    confusion(metadata, arguments.output)
    roc(metadata, arguments.output)
    class_metrics(metadata, arguments.output)


if __name__ == "__main__":
    main()
