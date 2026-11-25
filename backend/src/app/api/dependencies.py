"""Composición de dependencias: estado de la app, sesión por request, servicios y permisos."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.modules.auth.application.service import AuthService
from app.modules.auth.domain.role import Principal, Role
from app.modules.auth.infrastructure.security import PasswordHasher, TokenService
from app.modules.datasets.application.service import DatasetService
from app.modules.model_registry.application.active_model import ActiveModelProvider
from app.modules.model_registry.application.service import ModelRegistryService
from app.modules.prediction.application.service import PredictionService
from app.modules.training.application.service import TrainingService
from app.shared.errors import ForbiddenError, UnauthorizedError
from app.shared.rate_limit import RateLimiter


@dataclass
class AppState:
    settings: Settings
    sessions: sessionmaker[Session]
    hasher: PasswordHasher
    tokens: TokenService
    models: ActiveModelProvider
    prediction_limiter: RateLimiter
    login_limiter: RateLimiter


def get_state(request: Request) -> AppState:
    state: AppState = request.app.state.services
    return state


State = Annotated[AppState, Depends(get_state)]


def get_session(state: State) -> Iterator[Session]:
    """Una transacción por request: commit si todo sale bien, rollback si hay error."""
    with state.sessions.begin() as session:
        yield session


DbSession = Annotated[Session, Depends(get_session, scope="function")]


def auth_service(state: State, session: DbSession) -> AuthService:
    return AuthService(session, state.hasher, state.tokens)


def dataset_service(state: State, session: DbSession) -> DatasetService:
    max_bytes = state.settings.max_upload_megabytes * 1024 * 1024
    return DatasetService(session, state.settings.artifacts_directory, max_bytes)


def registry_service(session: DbSession) -> ModelRegistryService:
    return ModelRegistryService(session)


def prediction_service(state: State, session: DbSession) -> PredictionService:
    return PredictionService(session, state.models)


def training_service(
    session: DbSession, datasets: Annotated[DatasetService, Depends(dataset_service)]
) -> TrainingService:
    return TrainingService(session, datasets)


_bearer = HTTPBearer(auto_error=False, description="Token JWT obtenido en /auth/login")


def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    auth: Annotated[AuthService, Depends(auth_service)],
) -> Principal:
    if credentials is None:
        raise UnauthorizedError("Se requiere autenticación.")
    principal = auth.authenticate(credentials.credentials)
    if principal.role != Role.ADMIN:
        raise ForbiddenError("Se requiere rol de administrador.")
    return principal


Admin = Annotated[Principal, Depends(require_admin)]


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def limit_predictions(request: Request, state: State) -> None:
    state.prediction_limiter.check(_client_key(request))


def limit_logins(request: Request, state: State) -> None:
    state.login_limiter.check(_client_key(request))
