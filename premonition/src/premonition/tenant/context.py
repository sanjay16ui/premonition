"""Tenant context — request-scoped tenant isolation."""

from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass

DEFAULT_TENANT_ID = "premonition-default"
DEFAULT_TENANT_SLUG = "default"

_tenant_context: ContextVar["TenantContext | None"] = ContextVar("tenant_context", default=None)


@dataclass(frozen=True)
class TenantContext:
    """Active tenant for the current request."""

    tenant_id: str
    organization_id: str
    slug: str
    hospital_name: str = "Default Hospital"

    @property
    def is_default(self) -> bool:
        return self.tenant_id == DEFAULT_TENANT_ID


def get_default_tenant_id() -> str:
    return DEFAULT_TENANT_ID


def set_tenant_context(ctx: TenantContext) -> None:
    _tenant_context.set(ctx)


def get_tenant_context() -> TenantContext:
    ctx = _tenant_context.get()
    if ctx is None:
        return TenantContext(
            tenant_id=DEFAULT_TENANT_ID,
            organization_id="org-default",
            slug=DEFAULT_TENANT_SLUG,
            hospital_name="Default Hospital",
        )
    return ctx


def clear_tenant_context() -> None:
    _tenant_context.set(None)


def tenant_data_path(base: str, tenant_id: str | None = None) -> str:
    """Row-level security path pattern: tenants/{tenant_id}/{resource}."""
    tid = tenant_id or get_tenant_context().tenant_id
    return f"tenants/{tid}/{base}"
