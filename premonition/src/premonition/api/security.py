"""API security layer — unified JWT + API key authentication."""

from __future__ import annotations

import os

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from premonition.auth.dependencies import get_auth_context

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER = HTTPBearer(auto_error=False)

from starlette.requests import HTTPConnection

def get_configured_api_key() -> str | None:
    """Return legacy API key from environment. None = not configured."""
    return os.getenv("PREMONITION_API_KEY") or None


async def verify_api_key(conn: HTTPConnection) -> str | None:
    """
    Backward-compatible auth dependency used by existing routers.

    Delegates to unified JWT + API key auth. Returns subject when authenticated,
    None in dev mode (no JWT secret and no legacy API key).
    """
    api_key = conn.headers.get("x-api-key")
    if not api_key:
        api_key = conn.query_params.get("api_key")
        
    auth_header = conn.headers.get("authorization")
    bearer = None
    if auth_header and auth_header.lower().startswith("bearer "):
        bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials=auth_header[7:])
    elif conn.query_params.get("token"):
        bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials=conn.query_params.get("token"))
        
    ctx = await get_auth_context(api_key, bearer)
    if ctx.auth_method == "dev":
        return None
    return ctx.subject
