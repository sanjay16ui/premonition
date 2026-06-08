"""Tenant role hierarchy — extends platform RBAC with tenant-scoped roles."""

from __future__ import annotations

from enum import Enum

from premonition.auth.roles import ROLE_PERMISSIONS, Role, has_permission


class TenantRole(str, Enum):
    """Hierarchical tenant roles (highest to lowest privilege)."""
    PLATFORM_ADMIN = "platform_admin"
    ORG_ADMIN = "org_admin"
    HOSPITAL_ADMIN = "hospital_admin"
    DEPARTMENT_HEAD = "department_head"
    CLINICIAN = "clinician"
    EXECUTIVE = "executive"
    AUDITOR = "auditor"
    VIEWER = "viewer"


TENANT_ROLE_HIERARCHY: list[TenantRole] = [
    TenantRole.PLATFORM_ADMIN,
    TenantRole.ORG_ADMIN,
    TenantRole.HOSPITAL_ADMIN,
    TenantRole.DEPARTMENT_HEAD,
    TenantRole.CLINICIAN,
    TenantRole.EXECUTIVE,
    TenantRole.AUDITOR,
    TenantRole.VIEWER,
]

TENANT_ROLE_PERMISSIONS: dict[TenantRole, set[str]] = {
    TenantRole.PLATFORM_ADMIN: {
        "tenants:manage", "tenants:read", "orgs:manage", "orgs:read",
        "billing:read", "usage:read", "users:manage",
        "predict", "explain", "audit:read", "audit:write",
        "metrics:read", "models:read", "models:manage",
        "system:read", "realtime:read", "mlops:manage",
        "copilot:use", "copilot:read", "copilot:ingest", "copilot:executive",
    },
    TenantRole.ORG_ADMIN: {
        "tenants:manage", "tenants:read", "orgs:read",
        "billing:read", "usage:read", "users:manage",
        "predict", "explain", "audit:read", "metrics:read",
        "models:read", "system:read", "realtime:read",
        "copilot:use", "copilot:read", "copilot:ingest", "copilot:executive",
    },
    TenantRole.HOSPITAL_ADMIN: {
        "tenants:read", "usage:read", "users:manage",
        "predict", "explain", "audit:read", "metrics:read",
        "models:read", "system:read", "realtime:read", "mlops:manage",
        "copilot:use", "copilot:read", "copilot:ingest",
    },
    TenantRole.DEPARTMENT_HEAD: {
        "tenants:read", "predict", "explain", "audit:read",
        "metrics:read", "realtime:read",
        "copilot:use", "copilot:read",
    },
    TenantRole.CLINICIAN: ROLE_PERMISSIONS[Role.CLINICIAN] | {"tenants:read"},
    TenantRole.EXECUTIVE: ROLE_PERMISSIONS[Role.EXECUTIVE] | {"tenants:read", "billing:read"},
    TenantRole.AUDITOR: ROLE_PERMISSIONS[Role.AUDITOR] | {"tenants:read", "usage:read"},
    TenantRole.VIEWER: {"tenants:read", "metrics:read", "system:read", "copilot:read"},
}


def tenant_role_level(role: TenantRole) -> int:
    return TENANT_ROLE_HIERARCHY.index(role)


def can_manage_tenant(actor_role: TenantRole, target_role: TenantRole) -> bool:
    """Higher roles can manage lower roles within tenant."""
    return tenant_role_level(actor_role) < tenant_role_level(target_role)


def has_tenant_permission(role: TenantRole, permission: str) -> bool:
    return permission in TENANT_ROLE_PERMISSIONS.get(role, set())


def map_platform_role_to_tenant(role: Role) -> TenantRole:
    mapping = {
        Role.ADMIN: TenantRole.HOSPITAL_ADMIN,
        Role.CLINICIAN: TenantRole.CLINICIAN,
        Role.EXECUTIVE: TenantRole.EXECUTIVE,
        Role.AUDITOR: TenantRole.AUDITOR,
    }
    return mapping.get(role, TenantRole.VIEWER)


def effective_permission(role: Role, permission: str, is_platform_admin: bool = False) -> bool:
    if is_platform_admin:
        return True
    if has_permission(role, permission):
        return True
    tenant_role = map_platform_role_to_tenant(role)
    return has_tenant_permission(tenant_role, permission)
