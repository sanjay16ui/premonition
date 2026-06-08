"""Role-based access control definitions."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    CLINICIAN = "clinician"
    EXECUTIVE = "executive"
    AUDITOR = "auditor"


ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "predict", "explain", "audit:read", "audit:write",
        "metrics:read", "models:read", "models:manage",
        "system:read", "realtime:read", "users:manage", "mlops:manage",
        "copilot:use", "copilot:read", "copilot:ingest", "copilot:executive",
        "tenants:manage", "tenants:read", "orgs:manage", "orgs:read",
        "billing:read", "usage:read",
    },
    Role.CLINICIAN: {
        "predict", "explain", "audit:read", "metrics:read",
        "models:read", "system:read", "realtime:read",
        "copilot:use", "copilot:read", "copilot:ingest",
    },
    Role.EXECUTIVE: {
        "audit:read", "metrics:read", "models:read",
        "system:read", "realtime:read", "realtime:executive",
        "copilot:use", "copilot:read", "copilot:executive",
    },
    Role.AUDITOR: {
        "audit:read", "metrics:read", "models:read", "system:read",
        "copilot:read",
    },
}


def has_permission(role: Role, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
