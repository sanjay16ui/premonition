"""Tenant onboarding workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from premonition.tenant.isolation import tenant_subdir
from premonition.tenant.models import Organization, Tenant
from premonition.tenant.store import TenantStore


class TenantOnboardingService:
    """Orchestrate new hospital tenant provisioning."""

    def __init__(self, store: TenantStore, logs_dir: Path) -> None:
        self.store = store
        self.logs_dir = logs_dir

    def onboard(
        self,
        org_name: str,
        org_slug: str,
        org_email: str,
        hospital_name: str,
        tenant_slug: str,
        admin_email: str,
        admin_role: str = "hospital_admin",
        region: str = "us-east-1",
        plan: str = "standard",
        bed_capacity: int = 100,
        icu_beds: int = 20,
    ) -> dict[str, Any]:
        """Full onboarding: org → tenant → directories → admin member."""
        org = self.store.get_organization_by_slug(org_slug)
        if not org:
            org = self.store.create_organization(
                name=org_name, slug=org_slug,
                contact_email=org_email, region=region, plan=plan,
            )

        existing = self.store.get_tenant_by_slug(tenant_slug)
        if existing:
            raise ValueError(f"Tenant slug '{tenant_slug}' already exists")

        tenant = self.store.create_tenant(
            hospital_name=hospital_name,
            slug=tenant_slug,
            organization_id=org.id,
            bed_capacity=bed_capacity,
            icu_beds=icu_beds,
        )

        self._provision_tenant_directories(tenant)
        member = self.store.add_member(admin_email, admin_role, tenant.id)

        return {
            "organization": org,
            "tenant": tenant,
            "admin_member": member,
            "provisioned_paths": self._tenant_paths(tenant.id),
        }

    def _provision_tenant_directories(self, tenant: Tenant) -> None:
        """Create isolated data directories for tenant."""
        for subpath in ("audit", "copilot/conversations", "copilot/audit",
                        "models", "realtime", "analytics", "config"):
            tenant_subdir(self.logs_dir, subpath, tenant.id)

    def _tenant_paths(self, tenant_id: str) -> list[str]:
        root = self.logs_dir / "tenants" / tenant_id
        return [str(p) for p in root.rglob("*") if p.is_dir()]
