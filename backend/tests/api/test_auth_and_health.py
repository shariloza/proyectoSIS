import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import ADMIN_EMAIL, ADMIN_PASSWORD

pytestmark = pytest.mark.integration


def test_login_returns_bearer_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login", json={"email": ADMIN_EMAIL.upper(), "password": ADMIN_PASSWORD}
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] > 0


@pytest.mark.parametrize(
    "credentials",
    [
        {"email": ADMIN_EMAIL, "password": "wrong-password"},
        {"email": "nobody@test.local", "password": ADMIN_PASSWORD},
    ],
)
def test_login_with_bad_credentials_gives_same_generic_error(
    client: TestClient, credentials: dict[str, str]
) -> None:
    response = client.post("/api/v1/auth/login", json=credentials)

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Correo o contraseña incorrectos."


def test_readiness_reports_active_model(client: TestClient) -> None:
    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_version": "v1"}


def test_every_response_carries_a_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health/live", headers={"X-Request-ID": "trace-12345678"})

    assert response.headers["X-Request-ID"] == "trace-12345678"


def test_cors_only_allows_configured_origin(client: TestClient) -> None:
    allowed = client.options(
        "/api/v1/predictions",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    denied = client.options(
        "/api/v1/predictions",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )

    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in denied.headers


def test_unknown_route_uses_error_format(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
