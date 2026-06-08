"""In-memory rate limiting middleware."""

from __future__ import annotations

import os
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from premonition.api.schemas.errors import ErrorResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple token-bucket rate limiter per client IP.

    Configure via PREMONITION_RATE_LIMIT (requests per minute, default 120).
    Disabled when set to 0.
    """

    def __init__(self, app, requests_per_minute: int | None = None) -> None:
        super().__init__(app)
        limit = requests_per_minute or int(os.getenv("PREMONITION_RATE_LIMIT", "120"))
        self.enabled = limit > 0
        self.limit = limit
        self.window = 60.0
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.enabled or request.url.path.endswith("/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window

        bucket = self._buckets[client_ip]
        self._buckets[client_ip] = [t for t in bucket if t > window_start]

        if len(self._buckets[client_ip]) >= self.limit:
            body = ErrorResponse(
                error="rate_limit_exceeded",
                message=f"Rate limit exceeded ({self.limit} requests/minute)",
                request_id=getattr(request.state, "request_id", None),
            )
            return JSONResponse(status_code=429, content=body.model_dump())

        self._buckets[client_ip].append(now)
        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limit)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.limit - len(self._buckets[client_ip]))
        )
        return response
