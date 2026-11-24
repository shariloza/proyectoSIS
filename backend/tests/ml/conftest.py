from pathlib import Path

import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from app.ml.dataset import PreparedDataset, prepare
from app.ml.training import Candidate, default_candidates

DATASET_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "raw" / "student_depression_dataset.csv"
)


@pytest.fixture(scope="session")
def raw_full() -> pd.DataFrame:
    return pd.read_csv(DATASET_PATH)


@pytest.fixture
def raw(raw_full: pd.DataFrame) -> pd.DataFrame:
    """Muestra fija de 2.000 filas reales: rápida y representativa."""
    return raw_full.sample(n=2000, random_state=7).reset_index(drop=True)


@pytest.fixture
def prepared(raw: pd.DataFrame) -> PreparedDataset:
    return prepare(raw)


@pytest.fixture
def fast_candidates() -> list[Candidate]:
    """Dummy + un solo modelo, para tests rápidos del flujo completo."""
    dummy = default_candidates()[0]
    return [dummy, Candidate("LogisticRegression", LogisticRegression(max_iter=1000), {})]
