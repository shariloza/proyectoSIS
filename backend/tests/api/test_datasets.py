import pandas as pd
import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.config import Settings
from tests.machine_learning.conftest import DATASET_PATH

pytestmark = pytest.mark.integration

URL = "/api/v1/datasets"


def sample_csv_bytes(rows: int, seed: int) -> bytes:
    return pd.read_csv(DATASET_PATH).sample(n=rows, random_state=seed).to_csv(index=False).encode()


def upload(
    client: TestClient,
    headers: dict[str, str],
    content: bytes,
    name: str = "data.csv",
    content_type: str = "text/csv",
) -> Response:
    response: Response = client.post(
        URL, headers=headers, files={"file": (name, content, content_type)}
    )
    return response


def test_valid_csv_is_accepted_and_versioned(
    client: TestClient, admin_headers: dict[str, str], settings: Settings
) -> None:
    content = sample_csv_bytes(800, seed=21)

    response = upload(client, admin_headers, content)

    assert response.status_code == 201
    body = response.json()
    assert body["row_count"] == 800
    assert "Have you ever had suicidal thoughts ?" in body["validation_report"]["excluded_columns"]
    stored = settings.artifacts_directory / "datasets" / f"{body['sha256']}.csv"
    assert stored.read_bytes() == content


def test_duplicate_file_is_rejected(client: TestClient, admin_headers: dict[str, str]) -> None:
    content = sample_csv_bytes(700, seed=22)
    upload(client, admin_headers, content, name="a.csv")

    response = upload(client, admin_headers, content, name="b.csv")

    assert response.status_code == 409
    assert "dataset_id" in response.json()["error"]["details"]


def test_missing_columns_are_reported(client: TestClient, admin_headers: dict[str, str]) -> None:
    content = pd.read_csv(DATASET_PATH).head(600).drop(columns=["CGPA"]).to_csv(index=False)

    response = upload(client, admin_headers, content.encode())

    assert response.status_code == 422
    assert any("CGPA" in problem for problem in response.json()["error"]["details"])


def test_non_csv_is_rejected(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = upload(client, admin_headers, b"MZ\x90", "x.exe", "application/octet-stream")

    assert response.status_code == 415


def test_oversized_file_is_rejected(
    client: TestClient, admin_headers: dict[str, str], settings: Settings
) -> None:
    oversized = b"a" * (settings.max_upload_megabytes * 1024 * 1024 + 1)

    response = upload(client, admin_headers, oversized)

    assert response.status_code == 413


def test_unreadable_csv_is_rejected(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = upload(client, admin_headers, b"\x00\xff\xfe garbage")

    assert response.status_code == 422


def test_upload_requires_admin(client: TestClient) -> None:
    response = upload(client, {}, sample_csv_bytes(600, seed=23))

    assert response.status_code == 401
