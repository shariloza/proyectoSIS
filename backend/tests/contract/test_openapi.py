"""El contrato publicado (docs/openapi.json) debe coincidir con la API real."""

import json
from pathlib import Path
from typing import Any

import pytest

from app.openapi import openapi_document, render

PUBLISHED = Path(__file__).resolve().parents[3] / "docs" / "openapi.json"


@pytest.fixture(scope="module")
def document() -> dict[str, Any]:
    return openapi_document()


def test_published_contract_is_up_to_date(document: dict[str, Any]) -> None:
    assert PUBLISHED.read_text(encoding="utf-8") == render(document), (
        "docs/openapi.json está desactualizado: ejecutar `uv run python -m app.openapi "
        "../docs/openapi.json`"
    )


def test_all_required_operations_exist(document: dict[str, Any]) -> None:
    operations = {
        (method.upper(), path) for path, item in document["paths"].items() for method in item
    }
    assert {
        ("POST", "/api/v1/predictions"),
        ("GET", "/api/v1/predictions"),
        ("GET", "/api/v1/models/active"),
        ("GET", "/api/v1/models"),
        ("POST", "/api/v1/models/{model_id}/activate"),
        ("POST", "/api/v1/models/rollback"),
        ("POST", "/api/v1/datasets"),
        ("POST", "/api/v1/training-jobs"),
        ("GET", "/api/v1/training-jobs/{job_id}"),
        ("POST", "/api/v1/auth/login"),
        ("GET", "/api/v1/health/ready"),
    } <= operations


def test_every_operation_is_documented_with_errors(document: dict[str, Any]) -> None:
    for path, item in document["paths"].items():
        for method, operation in item.items():
            assert operation.get("summary"), f"{method} {path} sin summary"
            for status, response in operation["responses"].items():
                if status.startswith(("4", "5")) and status != "422":
                    schema = response["content"]["application/json"]["schema"]
                    assert schema == {"$ref": "#/components/schemas/ErrorResponse"}, (
                        f"{method} {path} {status}"
                    )


def test_prediction_input_exposes_allowed_categories(document: dict[str, Any]) -> None:
    profile = document["components"]["schemas"]["StudentProfileIn"]
    sleep = profile["properties"]["sleep_duration"]

    assert sleep["enum"] == ["Less than 5 hours", "5-6 hours", "7-8 hours", "More than 8 hours"]
    assert profile["additionalProperties"] is False
    assert "suicidal" not in json.dumps(profile).lower()
