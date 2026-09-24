import logging
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.errors import ApplicationError

logger = logging.getLogger("raizes.api")


def _error_body(
    request: Request,
    error: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> dict:
    return {
        "error": error,
        "message": message,
        "details": details or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "path": request.url.path,
        "requestId": getattr(request.state, "request_id", None),
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        errors = {
            401: "UNAUTHENTICATED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
        }
        return JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content=_error_body(
                request,
                errors.get(exc.status_code, "REQUEST_ERROR"),
                str(exc.detail),
            ),
        )

    @app.exception_handler(ApplicationError)
    async def handle_application_error(request: Request, exc: ApplicationError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(request, exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"] if part != "body"),
                "issue": error["msg"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body(
                request,
                "VALIDATION_ERROR",
                "Um ou mais campos são inválidos.",
                details,
            ),
        )

    @app.exception_handler(IntegrityError)
    async def handle_integrity_error(request: Request, _exc: IntegrityError):
        return JSONResponse(
            status_code=409,
            content=_error_body(
                request,
                "CONFLICT",
                "A operação conflita com dados já registrados ou com uma regra de integridade.",
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception(
            "Unhandled API error request_id=%s", request.state.request_id
        )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                request,
                "INTERNAL_ERROR",
                "Ocorreu um erro interno. Informe o requestId ao suporte.",
            ),
        )
