"""Global error handler — structured JSON error responses."""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _error_response(code: str, message: str, detail: str | None, status: int) -> JSONResponse:
    body: dict = {
        "error": {
            "code": code,
            "message": message,
            "status": status,
        }
    }
    if detail:
        body["error"]["detail"] = detail
    return JSONResponse(status_code=status, content=body)


def register_error_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code_map = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMITED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        return _error_response(code, str(exc.detail), None, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        detail = "; ".join(f"{e.get('loc', '')}: {e.get('msg', '')}" for e in errors[:5])
        return _error_response("VALIDATION_ERROR", "Request validation failed.", detail, 422)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return _error_response("BAD_REQUEST", str(exc), None, 400)

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method, request.url.path, exc, traceback.format_exc(),
        )
        return _error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred. Please try again.",
            None,
            500,
        )
