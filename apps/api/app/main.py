"""FastAPI app entry."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.config import get_settings
from app.routers import api_keys, decks, exports, images, me, projects, templates, uploads
from app.schemas.api import ErrorBody, ErrorResponse


def _configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )


def _configure_sentry() -> None:
    settings = get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
            environment=settings.env,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    _configure_sentry()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Present Yourself API",
        version="0.1.0",
        lifespan=lifespan,
        default_response_class=JSONResponse,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_mw(request: Request, call_next):
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=rid)
        resp = await call_next(request)
        resp.headers["x-request-id"] = rid
        return resp

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error=ErrorBody(code="INVALID_INPUT", message=str(exc))).model_dump(),
        )

    @app.get("/v1/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    api = FastAPI(title="v1")
    api.include_router(me.router)
    api.include_router(api_keys.router)
    api.include_router(projects.router)
    api.include_router(decks.router)
    api.include_router(templates.router)
    api.include_router(exports.router)
    api.include_router(images.router)
    api.include_router(uploads.router)

    app.mount("/v1", api)
    return app


app = create_app()
