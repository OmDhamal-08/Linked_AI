"""FastAPI application factory.

Run locally:  uvicorn app.main:app --reload
"""

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.models  # noqa: F401 - register ORM models with metadata
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging, get_logger, log_event, request_id_ctx
from app.db.session import ensure_schema, get_engine

logger = get_logger("app")


def _error_body(code: str, message: str, details=None) -> dict:
    body: dict = {"error": {"code": code, "message": message, "request_id": request_id_ctx.get()}}
    if details is not None:
        body["error"]["details"] = details
    return body


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    if settings.auto_create_tables:
        ensure_schema(get_engine())
    log_event(logger, logging.INFO, "app_started", environment=settings.environment)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description=settings.app_subtitle,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        token = request_id_ctx.set(rid)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            log_event(
                logger,
                logging.INFO,
                "http_request",
                method=request.method,
                endpoint=request.url.path,
                status=status_code,
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
                user_id=getattr(request.state, "user_id", None),
            )
            request_id_ctx.reset(token)

    @application.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        log_event(logger, logging.WARNING, "app_error", code=exc.code, status=exc.status_code)
        return JSONResponse(status_code=exc.status_code, content=_error_body(exc.code, exc.message, exc.details))

    @application.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(p) for p in err.get("loc", [])[1:]), "problem": err.get("msg", "")}
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_body("invalid_request", "Please check the highlighted fields and try again.", details),
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(_request: Request, exc: StarletteHTTPException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
        message = "We could not find what you were looking for." if exc.status_code == 404 else str(exc.detail)
        return JSONResponse(status_code=exc.status_code, content=_error_body(code, message))

    @application.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception):
        logger.exception("unhandled_error", extra={"fields": {"error": type(exc).__name__}})
        return JSONResponse(
            status_code=500,
            content=_error_body("internal_error", "Something went wrong. Please try again."),
        )

    application.include_router(api_router)

    @application.get("/", include_in_schema=False)
    def root():
        return {"name": settings.app_name, "docs": "/docs", "api": settings.api_prefix}

    return application


app = create_app()
