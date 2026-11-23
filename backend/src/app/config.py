"""Configuración de la aplicación leída de variables de entorno.

Falla al arrancar (fail fast) si falta una variable o tiene un valor inválido.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

# En desarrollo se lee el .env de la raíz del repositorio (compartido con docker-compose).
# En contenedores no existe y las variables llegan por el entorno.
ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class ConfigurationError(RuntimeError):
    """La configuración del entorno es incompleta o inválida."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", frozen=True)

    environment: Literal["development", "test", "production"]
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    postgres_host: str = Field(min_length=1)
    postgres_port: int = Field(ge=1, le=65535)
    postgres_db: str = Field(min_length=1)
    postgres_user: str = Field(min_length=1)
    postgres_password: SecretStr = Field(min_length=12)

    jwt_secret: SecretStr = Field(min_length=32)
    jwt_issuer: str = Field(min_length=1)
    jwt_audience: str = Field(min_length=1)
    jwt_expire_minutes: int = Field(ge=5, le=1440)

    admin_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    admin_password: SecretStr = Field(min_length=12)

    cors_origins: list[str] = Field(min_length=1)
    artifacts_dir: Path
    max_upload_mb: int = Field(ge=1, le=50)
    training_timeout_seconds: int = Field(ge=60, le=3600)

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


def load_settings(env_file: Path | None = ROOT_ENV_FILE) -> Settings:
    """Construye la configuración y traduce los errores a un mensaje legible."""
    try:
        return Settings(_env_file=env_file)
    except ValidationError as exc:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']).upper()}: {error['msg']}"
            for error in exc.errors()
        )
        raise ConfigurationError(f"Configuración inválida -> {problems}") from None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
