"""FastAPI auth dependencies — JWT + API key + RBAC."""

from __future__ import annotations

import os
import secrets
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from premonition.auth.jwt_handler import decode_token, is_jwt_enabled
from premonition.auth.rbac import AuthContext, require_permission
from premonition.auth.roles import Role
from premonition.auth.user_store import UserStore
from premonition.config.settings import get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER = HTTPBearer(auto_error=False)

_user_store: UserStore | None = None


def get_user_store() -> UserStore:
    global _user_store
    if _user_store is None:
        _user_store = UserStore(get_settings().logs_dir)
    return _user_store


def _legacy_api_key_configured() -> str | None:
    return os.getenv("PREMONITION_API_KEY") or None


async def get_auth_context(
    api_key: Annotated[str | None, Security(API_KEY_HEADER)],
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(BEARER)],
) -> AuthContext:
    """
    Unified authentication: JWT Bearer > managed API key > legacy API key > dev mode.
    """
    store = get_user_store()

    if bearer and bearer.credentials:
        if not is_jwt_enabled():
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "JWT not configured")
        try:
            payload = decode_token(bearer.credentials)
            if payload.get("type") != "access":
                raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
            return AuthContext(
                subject=payload["sub"],
                role=Role(payload["role"]),
                auth_method="jwt",
                tenant_id=payload.get("tenant_id"),
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc

    if api_key:
        role = store.verify_api_key(api_key)
        if role:
            return AuthContext(subject=f"apikey:{role.value}", role=role, auth_method="api_key")

        legacy = _legacy_api_key_configured()
        if legacy and secrets.compare_digest(api_key, legacy):
            return AuthContext(subject="legacy-api-key", role=Role.ADMIN, auth_method="api_key")

    if not is_jwt_enabled() and not _legacy_api_key_configured():
        return AuthContext(subject="dev", role=Role.ADMIN, auth_method="dev")

    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")


def require_roles(*roles: Role):
    async def _checker(ctx: Annotated[AuthContext, Depends(get_auth_context)]) -> AuthContext:
        if ctx.auth_method == "dev" or ctx.role == Role.ADMIN:
            return ctx
        if ctx.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requires one of: {[r.value for r in roles]}",
            )
        return ctx
    return _checker


def require_perm(permission: str):
    async def _checker(ctx: Annotated[AuthContext, Depends(get_auth_context)]) -> AuthContext:
        if ctx.auth_method != "dev":
            require_permission(ctx, permission)
        return ctx
    return _checker


AuthCtxDep = Annotated[AuthContext, Depends(get_auth_context)]
