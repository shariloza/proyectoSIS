import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.domain.role import Principal, Role
from app.modules.auth.infrastructure.records import AdminUserRecord
from app.modules.auth.infrastructure.security import InvalidTokenError, PasswordHasher, TokenService
from app.shared.errors import UnauthorizedError

INVALID_CREDENTIALS = "Correo o contraseña incorrectos."
INVALID_TOKEN = "Token inválido o expirado."  # noqa: S105 - mensaje, no secreto


class AuthService:
    def __init__(self, session: Session, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._session = session
        self._hasher = hasher
        self._tokens = tokens

    def login(self, email: str, password: str) -> str:
        user = self._find(email)
        if user is None:
            self._hasher.burn_time(password)
            raise UnauthorizedError(INVALID_CREDENTIALS)
        if not self._hasher.verify(user.password_hash, password) or not user.is_active:
            raise UnauthorizedError(INVALID_CREDENTIALS)
        return self._tokens.issue(user.id, user.role)

    def authenticate(self, token: str) -> Principal:
        try:
            claims = self._tokens.verify(token)
        except InvalidTokenError:
            raise UnauthorizedError(INVALID_TOKEN) from None

        user = self._session.get(AdminUserRecord, uuid.UUID(claims["sub"]))
        if user is None or not user.is_active:
            raise UnauthorizedError(INVALID_TOKEN)
        return Principal(id=user.id, email=user.email, role=Role(user.role))

    def ensure_admin(self, email: str, password: str) -> bool:
        """Crea el administrador inicial si no existe. Devuelve True si lo creó."""
        if self._find(email):
            return False
        self._session.add(
            AdminUserRecord(
                email=email.lower(), password_hash=self._hasher.hash(password), role=Role.ADMIN
            )
        )
        return True

    def _find(self, email: str) -> AdminUserRecord | None:
        return self._session.scalar(
            select(AdminUserRecord).where(AdminUserRecord.email == email.lower())
        )
