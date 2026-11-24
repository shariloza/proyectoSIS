"""Aplicación FastAPI.

Producción: `uvicorn app.main:production_app --factory`. Tests: `create_app(state)`.
"""

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import AppState
from app.api.errors import register_error_handlers
from app.config import Settings, get_settings
from app.modules.auth.infrastructure.security import PasswordHasher, TokenService
from app.modules.auth.presentation.router import router as auth_router
from app.modules.datasets.presentation.router import router as datasets_router
from app.modules.health.presentation.router import router as health_router
from app.modules.model_registry.application.active_model import ActiveModelProvider
from app.modules.model_registry.presentation.router import router as models_router
from app.modules.prediction.presentation.router import router as predictions_router
from app.modules.training.presentation.router import router as training_router
from app.shared.database import create_session_factory
from app.shared.logging import configure_logging, request_id_var
from app.shared.rate_limit import RateLimiter

API_PREFIX = "/api/v1"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")

logger = logging.getLogger("app.http")

DESCRIPTION = """
API del sistema de **estimación del riesgo de depresión en estudiantes**
(trabajo final TALLERSISIA).

> ⚠️ El resultado es una estimación estadística con fines académicos. **No es un diagnóstico.**

* **Público:** predicción, métricas del modelo activo y health.
* **Administración (JWT Bearer):** historial, datasets, re-entrenamiento, activación y rollback.

Todos los errores usan el formato `{"error": {"code", "message", "details", "request_id"}}`.
"""


def build_state(settings: Settings) -> AppState:
    return AppState(
        settings=settings,
        sessions=create_session_factory(settings.database_url),
        hasher=PasswordHasher(),
        tokens=TokenService(
            settings.jwt_secret.get_secret_value(),
            settings.jwt_issuer,
            settings.jwt_audience,
            settings.jwt_expire_minutes,
        ),
        models=ActiveModelProvider(settings.artifacts_dir),
        prediction_limiter=RateLimiter(max_requests=30, window_seconds=60),
        login_limiter=RateLimiter(max_requests=5, window_seconds=60),
    )


def create_app(state: AppState) -> FastAPI:
    app = FastAPI(
        title="API de riesgo de depresión estudiantil",
        version="1.0.0",
        description=DESCRIPTION,
        docs_url="/docs",
        redoc_url=None,
        openapi_url="/openapi.json",
    )
    app.state.services = state

    app.add_middleware(
        CORSMiddleware,
        allow_origins=state.settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get("X-Request-ID", "")
        request_id = incoming if REQUEST_ID_PATTERN.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
            },
        )
        return response

    register_error_handlers(app)
    for router in (
        predictions_router,
        models_router,
        datasets_router,
        training_router,
        auth_router,
        health_router,
    ):
        app.include_router(router, prefix=API_PREFIX)
    return app


def production_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    return create_app(build_state(settings))
