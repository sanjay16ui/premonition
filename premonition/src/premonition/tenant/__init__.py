"""Multi-tenant SaaS platform — hospital isolation and management."""

from premonition.tenant.context import TenantContext, get_default_tenant_id
from premonition.tenant.service import TenantService

__all__ = ["TenantContext", "TenantService", "get_default_tenant_id"]
