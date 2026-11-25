"""Hash de contraseñas (Argon2) y tokens JWT con validación completa."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from functools import cached_property
from typing import Any

import jwt
from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

ALGORITHM = "HS256"


class PasswordHasher:
    def __init__(self) -> None:
        self._argon2 = Argon2Hasher()

    def hash(self, password: str) -> str:
        return self._argon2.hash(password)

    def verify(self, password_hash: str, password: str) -> bool:
        try:
            return self._argon2.verify(password_hash, password)
        except (VerifyMismatchError, InvalidHashError):
            return False

    def burn_time(self, password: str) -> None:
        """Verificación ficticia para que un correo inexistente tarde lo mismo que uno válido."""
        self.verify(self._dummy_hash, password)

    @cached_property
    def _dummy_hash(self) -> str:
        return self._argon2.hash(secrets.token_hex(16))


class InvalidTokenError(Exception):
    pass


class TokenService:
    def __init__(self, secret: str, issuer: str, audience: str, expire_minutes: int) -> None:
        self._secret = secret
        self._issuer = issuer
        self._audience = audience
        self._ttl = timedelta(minutes=expire_minutes)

    @property
    def ttl_seconds(self) -> int:
        return int(self._ttl.total_seconds())

    def issue(self, subject: uuid.UUID, role: str) -> str:
        now = datetime.now(UTC)
        claims = {
            "sub": str(subject),
            "role": role,
            "iss": self._issuer,
            "aud": self._audience,
            "iat": now,
            "exp": now + self._ttl,
        }
        return jwt.encode(claims, self._secret, algorithm=ALGORITHM)

    def verify(self, token: str) -> dict[str, Any]:
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                issuer=self._issuer,
                audience=self._audience,
                options={"require": ["sub", "role", "iss", "aud", "exp", "iat"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidTokenError(str(exc)) from None
        return claims
