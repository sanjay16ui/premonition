"""Tenant service facade — unified multi-tenant operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from premonition.tenant.billing import BillingService
from premonition.tenant.config_manager import TenantConfigManager
from premonition.tenant.context import TenantContext, get_default_tenant_id
from premonition.tenant.models import Organization, Tenant
from premonition.tenant.onboarding import TenantOnboardingService
from premonition.tenant.store import TenantStore
from premonition.tenant.usage import UsageTracker


class TenantService:
    """Central service for multi-hospital SaaS operations."""

    def __init__(self, logs_dir: Path) -> None:
        self.store = TenantStore(logs_dir)
        self.billing = BillingService(self.store)
        self.usage = UsageTracker(self.store)
        self.config = TenantConfigManager(self.store)
        self.onboarding = TenantOnboardingService(self.store, logs_dir)

    def resolve_context(self, tenant_id: str | None = None, tenant_slug: str | None = None) -> TenantContext:
        tenant: Tenant | None = None
        if tenant_id:
            tenant = self.store.get_tenant(tenant_id)
        elif tenant_slug:
            tenant = self.store.get_tenant_by_slug(tenant_slug)
        else:
            tenant = self.store.get_tenant(get_default_tenant_id())

        if not tenant:
            tenant = self.store.get_tenant(get_default_tenant_id())
        assert tenant is not None

        return TenantContext(
            tenant_id=tenant.id,
            organization_id=tenant.organization_id,
            slug=tenant.slug,
            hospital_name=tenant.hospital_name,
        )

    def list_tenants(self, organization_id: str | None = None) -> list[Tenant]:
        return self.store.list_tenants(organization_id)

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self.store.get_tenant(tenant_id)

    def list_organizations(self) -> list[Organization]:
        return self.store.list_organizations()

    def get_organization(self, org_id: str) -> Organization | None:
        return self.store.get_organization(org_id)

    def onboard_hospital(self, **kwargs: Any) -> dict[str, Any]:
        return self.onboarding.onboard(**kwargs)

    def track_api_call(self, tenant_id: str) -> None:
        self.usage.track(tenant_id, "api_calls")

    def track_prediction(self, tenant_id: str) -> None:
        self.usage.track(tenant_id, "predictions")

    def track_copilot(self, tenant_id: str) -> None:
        self.usage.track(tenant_id, "copilot_requests")

    def track_analytics(self, tenant_id: str) -> None:
        self.usage.track(tenant_id, "analytics_queries")

    def track_realtime(self, tenant_id: str) -> None:
        self.usage.track(tenant_id, "realtime_events")
