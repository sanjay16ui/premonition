"""Tenant context middleware — extracts tenant from header or JWT."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from premonition.tenant.context import clear_tenant_context, set_tenant_context
from premonition.tenant.service import TenantService
from premonition.utils.logging import get_logger

logger = get_logger(__name__)

TENANT_HEADER = "X-Tenant-ID"
TENANT_SLUG_HEADER = "X-Tenant-Slug"


class TenantMiddleware(BaseHTTPMiddleware):
    """Inject tenant context into every request for RLS."""

    def __init__(self, app, tenant_service: TenantService) -> None:
        super().__init__(app)
        self.tenant_service = tenant_service

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tenant_id = request.headers.get(TENANT_HEADER)
        tenant_slug = request.headers.get(TENANT_SLUG_HEADER)

        # Also check JWT claim if present
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer ") and not tenant_id:
            try:
                from premonition.auth.jwt_handler import decode_token, is_jwt_enabled
                if is_jwt_enabled():
                    payload = decode_token(auth_header[7:])
                    tenant_id = payload.get("tenant_id")
            except Exception:
                pass

        try:
            ctx = self.tenant_service.resolve_context(tenant_id=tenant_id, tenant_slug=tenant_slug)
            set_tenant_context(ctx)
            request.state.tenant_id = ctx.tenant_id
            request.state.tenant_context = ctx
            self.tenant_service.track_api_call(ctx.tenant_id)
        except Exception as exc:
            logger.warning("Tenant context resolution failed: %s", exc)
            ctx = self.tenant_service.resolve_context()
            set_tenant_context(ctx)
            request.state.tenant_id = ctx.tenant_id

        try:
            response = await call_next(request)
            response.headers["X-Tenant-ID"] = request.state.tenant_id
            return response
        finally:
            clear_tenant_context()
