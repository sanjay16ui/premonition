"""Row-level security utilities for strict tenant isolation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

from premonition.tenant.context import TenantContext, get_tenant_context
from premonition.utils.paths import ensure_dir

T = TypeVar("T")


class TenantIsolationError(Exception):
    """Raised when cross-tenant access is attempted."""


def tenant_root(logs_dir: Path, tenant_id: str | None = None) -> Path:
    """Resolve isolated data directory for a tenant."""
    ctx = get_tenant_context()
    tid = tenant_id or ctx.tenant_id
    return ensure_dir(logs_dir / "tenants" / tid)


def tenant_subdir(logs_dir: Path, subpath: str, tenant_id: str | None = None) -> Path:
    """Resolve tenant-scoped subdirectory (audit, copilot, models, etc.)."""
    return ensure_dir(tenant_root(logs_dir, tenant_id) / subpath)


def assert_tenant_access(record_tenant_id: str, ctx: TenantContext | None = None) -> None:
    """Enforce row-level security — reject cross-tenant reads."""
    active = ctx or get_tenant_context()
    if record_tenant_id != active.tenant_id:
        raise TenantIsolationError(
            f"Access denied: record tenant '{record_tenant_id}' != active '{active.tenant_id}'"
        )


def filter_by_tenant(
    records: list[dict[str, Any]],
    tenant_id: str | None = None,
) -> list[dict[str, Any]]:
    """Filter records to active tenant (RLS pattern)."""
    tid = tenant_id or get_tenant_context().tenant_id
    return [r for r in records if r.get("tenant_id", tid) == tid]


def stamp_tenant(record: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
    """Stamp tenant_id on new records for RLS."""
    tid = tenant_id or get_tenant_context().tenant_id
    return {**record, "tenant_id": tid}
