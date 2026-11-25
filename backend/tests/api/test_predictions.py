import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import VALID_PROFILE

pytestmark = pytest.mark.integration

URL = "/api/v1/predictions"


def test_prediction_uses_active_model_and_is_stored(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.post(URL, json=VALID_PROFILE)

    assert response.status_code == 201
    body = response.json()
    assert body["model_version"] == "v1"
    assert body["prediction"] in (0, 1)
    assert 0 <= body["probability"] <= 1
    assert body["risk_band"] in ("LOW", "MODERATE", "HIGH")
    assert "NO es un diagnóstico" in body["disclaimer"]

    history = client.get(URL, params={"size": 100}, headers=admin_headers).json()
    stored = next(item for item in history["items"] if item["id"] == body["id"])
    assert stored["input"] == VALID_PROFILE
    assert stored["model_version"] == "v1"
    assert stored["probability"] == body["probability"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("age", 17),
        ("academic_pressure", 6),
        ("grade_point_average", 10.5),
        ("sleep_duration", "Others"),
        ("gender", "Unknown"),
    ],
)
def test_out_of_range_input_is_rejected(client: TestClient, field: str, value: object) -> None:
    response = client.post(URL, json=VALID_PROFILE | {field: value})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert any(detail["field"] == field for detail in error["details"])
    assert error["request_id"]


def test_sensitive_or_unknown_fields_are_rejected(client: TestClient) -> None:
    response = client.post(URL, json=VALID_PROFILE | {"suicidal_thoughts": "Yes"})

    assert response.status_code == 422


def test_history_requires_authentication(client: TestClient) -> None:
    response = client.get(URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_history_rejects_forged_token(client: TestClient) -> None:
    forged = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIn0.c2lnbmF0dXJhLWZhbHNh"
    response = client.get(URL, headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


def test_history_is_paginated(client: TestClient, admin_headers: dict[str, str]) -> None:
    for _ in range(3):
        client.post(URL, json=VALID_PROFILE)

    page = client.get(URL, params={"page": 1, "size": 2}, headers=admin_headers).json()

    assert page["size"] == 2
    assert len(page["items"]) == 2
    assert page["total"] >= 3
    dates = [item["created_at"] for item in page["items"]]
    assert dates == sorted(dates, reverse=True)


def test_history_rejects_invalid_page_size(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.get(URL, params={"size": 1000}, headers=admin_headers)

    assert response.status_code == 422
