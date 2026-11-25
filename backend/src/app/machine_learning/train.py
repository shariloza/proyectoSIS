"""Script de entrenamiento por línea de comandos.

Uso: python -m app.machine_learning.train --dataset <csv> --models-directory <dir> --version v1
"""

import argparse
import json
from pathlib import Path

from app.machine_learning.artifact import save_model
from app.machine_learning.dataset import prepare, read_csv
from app.machine_learning.training import train


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--models-directory", type=Path, required=True)
    parser.add_argument("--version", required=True)
    arguments = parser.parse_args()

    prepared = prepare(read_csv(arguments.dataset))
    result = train(prepared.features, prepared.target)
    metadata = save_model(
        result,
        models_directory=arguments.models_directory,
        version_name=arguments.version,
        dataset_path=arguments.dataset,
        preparation=prepared.report,
    )
    summary = {
        key: metadata[key] for key in ("version", "status", "algorithm", "hyperparameters")
    } | {
        "preparation": metadata["dataset"]["preparation"],
        "comparison": metadata["comparison"],
        "test": {
            name: value
            for name, value in metadata["metrics"]["test"].items()
            if name != "roc_curve"
        },
        "acceptance": metadata["acceptance"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
