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

from app.ml.dataset import prepare, read_csv

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


def target_distribution(data: pd.DataFrame, out: Path) -> None:
    counts = data["depression"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(
        [CLASS_LABELS[i] for i in counts.index], counts.values, color=[NO_RISK, RISK], width=0.55
    )
    for bar, value in zip(bars, counts.values, strict=True):
        ax.annotate(
            f"{value:,} ({value / counts.sum():.1%})".replace(",", "."),
            (bar.get_x() + bar.get_width() / 2, value),
            ha="center",
            va="bottom",
            color=INK,
            xytext=(0, 4),
            textcoords="offset points",
        )
    ax.set_title("Distribución de la variable objetivo")
    ax.set_ylabel("Estudiantes")
    ax.grid(axis="x", visible=False)
    _save(fig, out / "01_distribucion_objetivo.png")


def risk_factors(data: pd.DataFrame, out: Path) -> None:
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
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    for ax, (column, title, order) in zip(axes.flat, panels, strict=True):
        rate = data.groupby(column)["depression"].mean()
        if order:
            rate = rate.reindex(order)
        names = [
            labels_es.get(str(k), str(int(k)) if isinstance(k, float) else k) for k in rate.index
        ]
        ax.bar(names, rate.values * 100, color=RISK, width=0.6)
        ax.set_title(title)
        ax.set_ylim(0, 100)
        ax.grid(axis="x", visible=False)
    for ax in axes[:, 0]:
        ax.set_ylabel("% con depresión")
    fig.suptitle("Tasa de depresión según factores de riesgo", fontweight="bold", color=INK)
    fig.tight_layout()
    _save(fig, out / "02_factores_de_riesgo.png")


def correlations(data: pd.DataFrame, out: Path) -> None:
    numeric = data.select_dtypes("number")
    names = {
        "age": "Edad",
        "cgpa": "Promedio (CGPA)",
        "academic_pressure": "Presión académica",
        "study_satisfaction": "Satisfacción estudio",
        "work_study_hours": "Horas estudio/trabajo",
        "financial_stress": "Estrés financiero",
        "depression": "Depresión",
    }
    corr = numeric.rename(columns=names).corr()
    fig, ax = plt.subplots(figsize=(7.5, 6))
    image = ax.imshow(corr.values, cmap=DIVERGING, vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr)), corr.columns, rotation=40, ha="right")
    ax.set_yticks(range(len(corr)), corr.columns)
    ax.grid(visible=False)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", color=INK, fontsize=8)
    fig.colorbar(image, ax=ax, shrink=0.8, label="Correlación de Pearson")
    ax.set_title("Correlación entre variables numéricas")
    _save(fig, out / "03_correlaciones.png")


def model_comparison(metadata: dict[str, Any], out: Path) -> None:
    rows = metadata["comparison"]
    names = [r["algorithm"].replace("Classifier", "") for r in rows]
    metrics = [
        ("cv_roc_auc", "ROC-AUC (CV 5 pliegues)", NO_RISK),
        ("val_roc_auc", "ROC-AUC validación", RISK),
    ]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.36
    for offset, (key, label, color) in enumerate(metrics):
        positions = [i + (offset - 0.5) * (width + 0.02) for i in range(len(rows))]
        bars = ax.bar(positions, [r[key] for r in rows], width=width, color=color, label=label)
        ax.bar_label(bars, fmt="%.3f", fontsize=8, color=INK, padding=2)
    ax.axhline(0.85, color=INK_SECONDARY, linestyle="--", linewidth=1)
    ax.text(-0.4, 0.86, "criterio C1 = 0,85", color=INK_SECONDARY, ha="left", fontsize=8)
    ax.set_xticks(range(len(rows)), names)
    ax.set_ylim(0.4, 1.0)
    ax.set_ylabel("ROC-AUC")
    ax.set_title(f"Comparación de modelos (elegido: {metadata['algorithm']})")
    ax.legend(frameon=False, loc="upper left")
    ax.grid(axis="x", visible=False)
    _save(fig, out / "04_comparacion_modelos.png")


def confusion(metadata: dict[str, Any], out: Path) -> None:
    matrix = metadata["metrics"]["test"]["confusion_matrix"]
    fig, ax = plt.subplots(figsize=(5.5, 4.8))
    ax.imshow(matrix, cmap=SEQUENTIAL)
    labels = list(CLASS_LABELS.values())
    ax.set_xticks([0, 1], labels)
    ax.set_yticks([0, 1], labels)
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Valor real")
    ax.grid(visible=False)
    total = sum(map(sum, matrix))
    darkest = max(map(max, matrix))
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                f"{matrix[i][j]:,}\n{matrix[i][j] / total:.1%}".replace(",", "."),
                ha="center",
                va="center",
                color=SURFACE if matrix[i][j] > darkest * 0.7 else INK,
                fontsize=11,
                fontweight="bold",
            )
    ax.set_title(f"Matriz de confusión — test ({metadata['version']})")
    _save(fig, out / "05_matriz_confusion.png")


def roc(metadata: dict[str, Any], out: Path) -> None:
    curve = metadata["metrics"]["test"]["roc_curve"]
    auc = metadata["metrics"]["test"]["roc_auc"]
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot(
        curve["fpr"],
        curve["tpr"],
        color=NO_RISK,
        linewidth=2,
        label=f"{metadata['algorithm']} (AUC = {auc:.3f})",
    )
    ax.plot(
        [0, 1], [0, 1], color=INK_SECONDARY, linestyle="--", linewidth=1, label="Azar (AUC = 0,5)"
    )
    ax.set_xlabel("Tasa de falsos positivos")
    ax.set_ylabel("Tasa de verdaderos positivos (recall)")
    ax.set_title("Curva ROC — conjunto de test")
    ax.legend(frameon=False, loc="lower right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.01)
    _save(fig, out / "06_curva_roc.png")


def class_metrics(metadata: dict[str, Any], out: Path) -> None:
    per_class = metadata["metrics"]["test"]["per_class"]
    metrics = [("precision", "Precisión"), ("recall", "Recall"), ("f1", "F1")]
    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.36
    for offset, (label, color) in enumerate(((0, NO_RISK), (1, RISK))):
        positions = [i + (offset - 0.5) * (width + 0.02) for i in range(len(metrics))]
        values = [per_class[str(label)][key] for key, _ in metrics]
        bars = ax.bar(positions, values, width=width, color=color, label=CLASS_LABELS[label])
        ax.bar_label(bars, fmt="%.3f", fontsize=8, color=INK, padding=2)
    ax.set_xticks(range(len(metrics)), [name for _, name in metrics])
    ax.set_ylim(0, 1)
    ax.set_title("Métricas por clase — conjunto de test")
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="x", visible=False)
    _save(fig, out / "07_metricas_por_clase.png")


def _save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path)
    plt.close(fig)
    print(f"generada {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    prepared = prepare(read_csv(args.dataset))
    data = prepared.features.assign(depression=prepared.target)
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))

    target_distribution(data, args.output)
    risk_factors(data, args.output)
    correlations(data, args.output)
    model_comparison(metadata, args.output)
    confusion(metadata, args.output)
    roc(metadata, args.output)
    class_metrics(metadata, args.output)


if __name__ == "__main__":
    main()
