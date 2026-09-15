from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import api_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.domain.models import HealthResponse
from app.repositories.change_repository import ChangeRepository, InMemoryChangeRepository
from app.services.solar_client import FakeSolarClient, SolarClient, UpstageSolarClient


logger = logging.getLogger("changespec_reviewer")


def _error_body(
    request: Request,
    *,
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "details": details,
        "requestId": getattr(request.state, "request_id", str(uuid.uuid4())),
    }


def _build_solar_client(settings: Settings) -> SolarClient:
    if settings.solar_mode == "fake":
        return FakeSolarClient()
    return UpstageSolarClient(settings)


def create_app(
    *,
    settings: Settings | None = None,
    repository: ChangeRepository | None = None,
    solar_client: SolarClient | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    application = FastAPI(
        title="ChangeSpec Reviewer API",
        version="0.1.0",
        description="Reviews whether operational PostgreSQL changes preserve the confirmed intent.",
    )
    application.state.change_repository = repository or InMemoryChangeRepository()
    application.state.solar_client = solar_client or _build_solar_client(resolved_settings)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    @application.middleware("http")
    async def attach_request_id(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                request,
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        details = [
            {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body(
                request,
                code="REQUEST_VALIDATION_ERROR",
                message="Request validation failed",
                details=details,
            ),
        )

    @application.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            code = str(exc.detail.get("code", "HTTP_ERROR"))
            message = str(exc.detail.get("message", "HTTP request failed"))
            details = exc.detail.get("details")
        else:
            code, message, details = "HTTP_ERROR", str(exc.detail), None
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(request, code=code, message=message, details=details),
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled request failure request_id=%s", request.state.request_id)
        return JSONResponse(
            status_code=500,
            content=_error_body(
                request,
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred",
            ),
        )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="changespec-reviewer", version="0.1.0")

    application.include_router(api_router, prefix="/api/v1")
    return application


app = create_app()
