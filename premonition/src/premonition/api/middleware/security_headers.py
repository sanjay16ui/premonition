"""Security headers and CSRF strategy middleware."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Apply OWASP-recommended security headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class CsrfProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF strategy for SPA + API:
    - Safe methods (GET/HEAD/OPTIONS) pass through
    - Mutating requests require X-Requested-With: XMLHttpRequest or Bearer token
    """

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request: Request, call_next) -> Response:
        from premonition.auth.jwt_handler import is_jwt_enabled

        if not is_jwt_enabled():
            return await call_next(request)

        if request.url.path.startswith("/api/v1/auth"):
            return await call_next(request)

        if request.method not in self.SAFE_METHODS:
            has_bearer = request.headers.get("Authorization", "").startswith("Bearer ")
            has_api_key = bool(request.headers.get("X-API-Key"))
            is_xhr = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            if not (has_bearer or has_api_key or is_xhr):
                return Response(
                    content='{"detail":"CSRF protection: missing auth header"}',
                    status_code=403,
                    media_type="application/json",
                )
        return await call_next(request)
