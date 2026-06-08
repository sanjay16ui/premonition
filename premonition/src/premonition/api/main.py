"""PREMONITION FastAPI application entrypoint."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from premonition.api.errors import register_exception_handlers
from premonition.api.lifespan import lifespan
from premonition.api.middleware import LoggingMiddleware, RateLimitMiddleware, TracingMiddleware
from premonition.api.middleware.security_headers import CsrfProtectionMiddleware, SecurityHeadersMiddleware
from premonition.api.routes import analytics, audit, auth, copilot, explain, health, metrics, mlops, models, predict, realtime, system, tenants
from premonition.api.version import API_PREFIX

APP_VERSION = "0.1.0"
APP_TITLE = "PREMONITION API"
APP_DESCRIPTION = """
**PREMONITION** — Real-time AI early-warning ICU sepsis prediction system.

## Features
- Automatic best-model loading from registry
- SHAP-based explainability
- Audit logging for every prediction
- Prometheus-compatible metrics
- Real-time ICU monitoring with SSE/WebSocket streaming
- Alert engine with 5-level escalation (GREEN → BLACK)
- AI recommendation engine with explainable outputs

## Authentication
Set `PREMONITION_API_KEY` environment variable to enable API key auth.
Pass the key in the `X-API-Key` header. When unset, auth is disabled (dev mode).
"""


def create_app() -> FastAPI:
    """Application factory — used by uvicorn and tests."""
    app = FastAPI(
        title=APP_TITLE,
        description=APP_DESCRIPTION,
        version=APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    cors_origins = os.getenv("PREMONITION_CORS_ORIGINS", "*").split(",")

    # Middleware — last added runs first (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Requested-With", "X-Request-ID", "X-Tenant-ID", "X-Tenant-Slug"],
    )
    # Tenant middleware added after app creation but needs tenant_service from lifespan
    @app.middleware("http")
    async def tenant_context_middleware(request, call_next):
        tenant_svc = getattr(request.app.state, "tenant_service", None)
        if tenant_svc is None:
            return await call_next(request)
        from premonition.tenant.middleware import TENANT_HEADER, TENANT_SLUG_HEADER
        from premonition.tenant.context import clear_tenant_context, set_tenant_context
        tenant_id = request.headers.get(TENANT_HEADER)
        tenant_slug = request.headers.get(TENANT_SLUG_HEADER)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and not tenant_id:
            try:
                from premonition.auth.jwt_handler import decode_token, is_jwt_enabled
                if is_jwt_enabled():
                    payload = decode_token(auth_header[7:])
                    tenant_id = payload.get("tenant_id")
            except Exception:
                pass
        ctx = tenant_svc.resolve_context(tenant_id=tenant_id, tenant_slug=tenant_slug)
        set_tenant_context(ctx)
        request.state.tenant_id = ctx.tenant_id
        request.state.tenant_context = ctx
        tenant_svc.track_api_call(ctx.tenant_id)
        try:
            response = await call_next(request)
            response.headers["X-Tenant-ID"] = ctx.tenant_id
            return response
        finally:
            clear_tenant_context()

    app.add_middleware(CsrfProtectionMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(TracingMiddleware)

    register_exception_handlers(app)

    # Versioned API routes
    app.include_router(health.router, prefix=API_PREFIX)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(system.router, prefix=API_PREFIX)
    app.include_router(models.router, prefix=API_PREFIX)
    app.include_router(predict.router, prefix=API_PREFIX)
    app.include_router(explain.router, prefix=API_PREFIX)
    app.include_router(audit.router, prefix=API_PREFIX)
    app.include_router(metrics.router, prefix=API_PREFIX)
    app.include_router(realtime.router, prefix=API_PREFIX)
    app.include_router(mlops.router, prefix=API_PREFIX)
    app.include_router(analytics.router, prefix=API_PREFIX)
    app.include_router(copilot.router, prefix=API_PREFIX)
    app.include_router(tenants.router, prefix=API_PREFIX)
    app.include_router(tenants.org_router, prefix=API_PREFIX)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": "premonition-api",
            "version": APP_VERSION,
            "docs": "/docs",
            "api": API_PREFIX,
        }

    @app.get("/health", include_in_schema=False)
    async def root_health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "premonition-api",
            "version": APP_VERSION,
        }

    return app


app = create_app()
