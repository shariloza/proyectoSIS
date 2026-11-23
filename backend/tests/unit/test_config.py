from functools import partial

import pytest

from app import config
from app.config import ConfigurationError

# Ignora el .env real: cada test controla su propio entorno.
load_settings = partial(config.load_settings, env_file=None)

VALID_ENV = {
    "ENVIRONMENT": "test",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "db",
    "POSTGRES_USER": "user",
    "POSTGRES_PASSWORD": "p@ss/word:123",
    "JWT_SECRET": "x" * 32,
    "JWT_ISSUER": "issuer",
    "JWT_AUDIENCE": "audience",
    "JWT_EXPIRE_MINUTES": "60",
    "ADMIN_EMAIL": "admin@example.com",
    "ADMIN_PASSWORD": "a-strong-password",
    "CORS_ORIGINS": '["http://localhost:5173"]',
    "ARTIFACTS_DIR": "./artifacts",
    "MAX_UPLOAD_MB": "10",
    "TRAINING_TIMEOUT_SECONDS": "900",
}


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Parte de una configuración válida que cada test modifica."""
    for key, value in VALID_ENV.items():
        monkeypatch.setenv(key, value)
    return monkeypatch


def test_valid_environment_builds_settings(env: pytest.MonkeyPatch) -> None:
    settings = load_settings()

    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.postgres_password.get_secret_value() not in repr(settings)


def test_database_url_escapes_special_characters(env: pytest.MonkeyPatch) -> None:
    url = load_settings().database_url

    assert url.password == "p@ss/word:123"
    assert url.drivername == "postgresql+psycopg"


def test_missing_variable_fails_fast_naming_it(env: pytest.MonkeyPatch) -> None:
    env.delenv("JWT_SECRET")

    with pytest.raises(ConfigurationError, match="JWT_SECRET"):
        load_settings()


@pytest.mark.parametrize(
    ("variable", "value"),
    [
        ("JWT_SECRET", "too-short"),
        ("POSTGRES_PORT", "70000"),
        ("ADMIN_EMAIL", "not-an-email"),
        ("ENVIRONMENT", "staging"),
        ("MAX_UPLOAD_MB", "500"),
    ],
)
def test_invalid_value_fails_fast(env: pytest.MonkeyPatch, variable: str, value: str) -> None:
    env.setenv(variable, value)

    with pytest.raises(ConfigurationError, match=variable):
        load_settings()
