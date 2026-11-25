"""Formato único de error: {"error": {"code", "message", "details", "request_id"}}."""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.errors import AppError
from app.shared.logging import request_id_context

logger = logging.getLogger(__name__)

HTTP_CODES = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    413: "PAYLOAD_TOO_LARGE",
}


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def error_response(status: int, code: str, message: str, details: Any = None) -> JSONResponse:
    body = ErrorBody(
        code=code, message=message, details=details, request_id=request_id_context.get()
    )
    return JSONResponse(ErrorResponse(error=body).model_dump(), status_code=status)


def documented_errors(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """Documenta en OpenAPI las respuestas de error de un endpoint."""
    descriptions = {
        401: "No autenticado o token inválido",
        403: "Sin permisos de administrador",
        404: "Recurso no encontrado",
        409: "Conflicto con el estado actual",
        413: "Archivo demasiado grande",
        415: "Tipo de archivo no soportado",
        422: "Datos de entrada inválidos",
        429: "Demasiadas solicitudes",
        503: "Servicio no disponible (sin modelo activo o base de datos caída)",
    }
    return {s: {"model": ErrorResponse, "description": descriptions[s]} for s in statuses}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(_: Request, error: AppError) -> JSONResponse:
        return error_response(error.status_code, error.code, error.message, error.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(str(part) for part in issue["loc"][1:]), "message": issue["msg"]}
            for issue in error.errors()
        ]
        return error_response(
            422, "VALIDATION_ERROR", "Los datos enviados no son válidos.", details
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, error: StarletteHTTPException) -> JSONResponse:
        code = HTTP_CODES.get(error.status_code, "HTTP_ERROR")
        return error_response(error.status_code, code, str(error.detail))

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, error: Exception) -> JSONResponse:
        logger.exception("error no controlado")
        return error_response(500, "INTERNAL_ERROR", "Ocurrió un error inesperado.")
