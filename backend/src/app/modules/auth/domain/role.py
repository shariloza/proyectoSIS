import uuid
from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"


@dataclass(frozen=True)
class Principal:
    """Usuario autenticado a partir de un token verificado."""

    id: uuid.UUID
    email: str
    role: Role
