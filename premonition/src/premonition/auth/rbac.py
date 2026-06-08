"""RBAC enforcement helpers."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from premonition.auth.roles import Role, has_permission


@dataclass
class AuthContext:
    """Authenticated principal."""

    subject: str
    role: Role
    auth_method: str  # "jwt" | "api_key" | "dev"
    tenant_id: str | None = None


def require_permission(ctx: AuthContext, permission: str) -> None:
    if not has_permission(ctx.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{ctx.role.value}' lacks permission '{permission}'",
        )
