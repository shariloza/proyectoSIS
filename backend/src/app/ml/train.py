"""CLI de entrenamiento.

Uso: python -m app.ml.train --dataset <csv> --models-dir <dir> --version v1
"""

import argparse
import json
from pathlib import Path

from app.ml.artifact import save_model
from app.ml.dataset import prepare, read_csv
from app.ml.training import train


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--models-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    prepared = prepare(read_csv(args.dataset))
    result = train(prepared.features, prepared.target)
    metadata = save_model(
        result,
        models_dir=args.models_dir,
        version_name=args.version,
        dataset_path=args.dataset,
        preparation=prepared.report,
    )
    summary = {
        key: metadata[key] for key in ("version", "status", "algorithm", "hyperparameters")
    } | {
        "preparation": metadata["dataset"]["preparation"],
        "comparison": metadata["comparison"],
        "test": {k: v for k, v in metadata["metrics"]["test"].items() if k != "roc_curve"},
        "acceptance": metadata["acceptance"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
