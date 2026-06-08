"""Centralized API error handling."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from premonition.api.schemas.errors import ErrorDetail, ErrorResponse
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


class APIError(Exception):
    """Base application error with HTTP status code."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error: str = "api_error",
        details: list[ErrorDetail] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error = error
        self.details = details or []
        super().__init__(message)


class ModelNotLoadedError(APIError):
    def __init__(self, message: str = "ML model is not loaded") -> None:
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE, "model_not_loaded")


class ValidationFailedError(APIError):
    def __init__(self, details: list[ErrorDetail]) -> None:
        super().__init__(
            "Request validation failed",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            details,
        )


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        body = ErrorResponse(
            error=exc.error,
            message=exc.message,
            request_id=_request_id(request),
            details=exc.details,
        )
        logger.warning("APIError [%s]: %s", exc.error, exc.message)
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        body = ErrorResponse(
            error="http_error",
            message=str(exc.detail),
            request_id=_request_id(request),
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=".".join(str(loc) for loc in e["loc"]),
                message=e["msg"],
                code=e["type"],
            )
            for e in exc.errors()
        ]
        body = ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            request_id=_request_id(request),
            details=details,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=body.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        body = ErrorResponse(
            error="internal_error",
            message="An unexpected error occurred",
            request_id=_request_id(request),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body.model_dump(),
        )
