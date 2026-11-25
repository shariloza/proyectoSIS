from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import AppState, auth_service, get_state, limit_logins
from app.api.errors import doc
from app.modules.auth.application.service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


class LoginIn(BaseModel):
    email: str = Field(max_length=254, examples=["admin@example.com"])
    password: str = Field(min_length=1, max_length=128, examples=["una-contraseña-segura"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105 - tipo de token, no secreto
    expires_in: int = Field(description="Segundos hasta que expira el token")


@router.post(
    "/login",
    summary="Iniciar sesión como administrador",
    description=(
        "Devuelve un JWT para las rutas de administración. Limitado a 5 intentos/min por IP."
    ),
    response_model=TokenOut,
    responses=doc(401, 422, 429),
    dependencies=[Depends(limit_logins)],
)
def login(
    body: LoginIn,
    auth: Annotated[AuthService, Depends(auth_service)],
    state: Annotated[AppState, Depends(get_state)],
) -> TokenOut:
    token = auth.login(body.email, body.password)
    return TokenOut(access_token=token, expires_in=state.tokens.ttl_seconds)
