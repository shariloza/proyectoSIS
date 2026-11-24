"""Errores de aplicación. La capa HTTP los traduce a un formato de respuesta único."""

from typing import Any


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class InvalidInputError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class PayloadTooLargeError(AppError):
    status_code = 413
    code = "PAYLOAD_TOO_LARGE"


class UnsupportedMediaTypeError(AppError):
    status_code = 415
    code = "UNSUPPORTED_MEDIA_TYPE"


class RateLimitedError(AppError):
    status_code = 429
    code = "RATE_LIMITED"


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "SERVICE_UNAVAILABLE"
