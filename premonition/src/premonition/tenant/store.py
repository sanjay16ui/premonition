"""File-backed tenant and organization store."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from premonition.tenant.context import DEFAULT_TENANT_ID
from premonition.tenant.models import BillingPlan, Organization, Tenant, TenantMember, TenantUsageRecord
from premonition.utils.paths import ensure_dir


class TenantStore:
    """Persistent store for organizations, tenants, members, billing, usage."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = ensure_dir(data_dir / "tenants")
        self.orgs_file = self.data_dir / "organizations.json"
        self.tenants_file = self.data_dir / "tenants.json"
        self.members_file = self.data_dir / "members.json"
        self.billing_file = self.data_dir / "billing.json"
        self.usage_file = self.data_dir / "usage.json"
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if not self.orgs_file.exists():
            default_org = Organization(
                id="org-default",
                name="PREMONITION Health System",
                slug="premonition",
                contact_email="admin@premonition.health",
            )
            self._save_orgs([default_org])

        if not self.tenants_file.exists():
            default_tenant = Tenant(
                id=DEFAULT_TENANT_ID,
                hospital_name="Default Hospital",
                slug="default",
                organization_id="org-default",
                config={
                    "model_tier": "t1",
                    "realtime_enabled": True,
                    "copilot_enabled": True,
                    "analytics_enabled": True,
                },
            )
            self._save_tenants([default_tenant])

        if not self.billing_file.exists():
            self._save_billing([
                BillingPlan(tenant_id=DEFAULT_TENANT_ID, plan="enterprise"),
            ])

    def _read_json(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, data: list[dict[str, Any]]) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _save_orgs(self, orgs: list[Organization]) -> None:
        self._write_json(self.orgs_file, [
            {
                "id": o.id, "name": o.name, "slug": o.slug,
                "contact_email": o.contact_email, "region": o.region,
                "plan": o.plan, "status": o.status, "created_at": o.created_at,
            }
            for o in orgs
        ])

    def _save_tenants(self, tenants: list[Tenant]) -> None:
        self._write_json(self.tenants_file, [
            {
                "id": t.id, "hospital_name": t.hospital_name, "slug": t.slug,
                "organization_id": t.organization_id, "timezone": t.timezone,
                "bed_capacity": t.bed_capacity, "icu_beds": t.icu_beds,
                "status": t.status, "created_at": t.created_at, "config": t.config,
            }
            for t in tenants
        ])

    def list_organizations(self) -> list[Organization]:
        return [Organization(**o) for o in self._read_json(self.orgs_file)]

    def get_organization(self, org_id: str) -> Organization | None:
        for o in self.list_organizations():
            if o.id == org_id:
                return o
        return None

    def get_organization_by_slug(self, slug: str) -> Organization | None:
        for o in self.list_organizations():
            if o.slug == slug:
                return o
        return None

    def create_organization(self, name: str, slug: str, contact_email: str,
                            region: str = "us-east-1", plan: str = "standard") -> Organization:
        org = Organization(
            id=f"org-{uuid.uuid4().hex[:12]}",
            name=name, slug=slug, contact_email=contact_email,
            region=region, plan=plan,
        )
        orgs = self.list_organizations()
        orgs.append(org)
        self._save_orgs(orgs)
        return org

    def list_tenants(self, organization_id: str | None = None) -> list[Tenant]:
        tenants = [Tenant(**t) for t in self._read_json(self.tenants_file)]
        if organization_id:
            tenants = [t for t in tenants if t.organization_id == organization_id]
        return tenants

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        for t in self.list_tenants():
            if t.id == tenant_id:
                return t
        return None

    def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        for t in self.list_tenants():
            if t.slug == slug:
                return t
        return None

    def create_tenant(
        self,
        hospital_name: str,
        slug: str,
        organization_id: str,
        timezone: str = "UTC",
        bed_capacity: int = 100,
        icu_beds: int = 20,
        config: dict[str, Any] | None = None,
    ) -> Tenant:
        tenant = Tenant(
            id=f"tenant-{uuid.uuid4().hex[:12]}",
            hospital_name=hospital_name,
            slug=slug,
            organization_id=organization_id,
            timezone=timezone,
            bed_capacity=bed_capacity,
            icu_beds=icu_beds,
            config=config or {
                "model_tier": "t1",
                "realtime_enabled": True,
                "copilot_enabled": True,
                "analytics_enabled": True,
            },
        )
        tenants = self.list_tenants()
        tenants.append(tenant)
        self._save_tenants(tenants)
        self._save_billing(self.list_billing() + [
            BillingPlan(tenant_id=tenant.id, plan="standard"),
        ])
        return tenant

    def update_tenant_config(self, tenant_id: str, config: dict[str, Any]) -> Tenant | None:
        tenants = self.list_tenants()
        for i, t in enumerate(tenants):
            if t.id == tenant_id:
                merged = {**t.config, **config}
                tenants[i] = Tenant(
                    id=t.id, hospital_name=t.hospital_name, slug=t.slug,
                    organization_id=t.organization_id, timezone=t.timezone,
                    bed_capacity=t.bed_capacity, icu_beds=t.icu_beds,
                    status=t.status, created_at=t.created_at, config=merged,
                )
                self._save_tenants(tenants)
                return tenants[i]
        return None

    def deactivate_tenant(self, tenant_id: str) -> Tenant | None:
        tenants = self.list_tenants()
        for i, t in enumerate(tenants):
            if t.id == tenant_id:
                tenants[i] = Tenant(
                    id=t.id, hospital_name=t.hospital_name, slug=t.slug,
                    organization_id=t.organization_id, timezone=t.timezone,
                    bed_capacity=t.bed_capacity, icu_beds=t.icu_beds,
                    status="inactive", created_at=t.created_at, config=t.config,
                )
                self._save_tenants(tenants)
                return tenants[i]
        return None

    # Members
    def list_members(self, tenant_id: str | None = None) -> list[TenantMember]:
        members = [TenantMember(**m) for m in self._read_json(self.members_file)]
        if tenant_id:
            members = [m for m in members if m.tenant_id == tenant_id]
        return members

    def add_member(self, email: str, role: str, tenant_id: str) -> TenantMember:
        member = TenantMember(email=email, role=role, tenant_id=tenant_id)
        members = self.list_members()
        members = [m for m in members if not (m.email == email and m.tenant_id == tenant_id)]
        members.append(member)
        self._write_json(self.members_file, [
            {"email": m.email, "role": m.role, "tenant_id": m.tenant_id, "active": m.active}
            for m in members
        ])
        return member

    # Billing
    def list_billing(self) -> list[BillingPlan]:
        return [BillingPlan(**b) for b in self._read_json(self.billing_file)]

    def get_billing(self, tenant_id: str) -> BillingPlan | None:
        for b in self.list_billing():
            if b.tenant_id == tenant_id:
                return b
        return None

    def _save_billing(self, plans: list[BillingPlan]) -> None:
        self._write_json(self.billing_file, [
            {
                "tenant_id": p.tenant_id, "plan": p.plan,
                "monthly_limit_predictions": p.monthly_limit_predictions,
                "monthly_limit_copilot": p.monthly_limit_copilot,
                "monthly_limit_api_calls": p.monthly_limit_api_calls,
                "overage_allowed": p.overage_allowed,
            }
            for p in plans
        ])

    # Usage
    def list_usage(self, tenant_id: str | None = None) -> list[TenantUsageRecord]:
        records = [TenantUsageRecord(**u) for u in self._read_json(self.usage_file)]
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        return records

    def get_usage(self, tenant_id: str, period: str) -> TenantUsageRecord:
        for r in self.list_usage(tenant_id):
            if r.period == period:
                return r
        return TenantUsageRecord(tenant_id=tenant_id, period=period)

    def increment_usage(self, tenant_id: str, metric: str, amount: int = 1) -> TenantUsageRecord:
        from datetime import datetime, timezone
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        records = self.list_usage()
        found = False
        result: TenantUsageRecord | None = None
        for i, r in enumerate(records):
            if r.tenant_id == tenant_id and r.period == period:
                data = {
                    "tenant_id": r.tenant_id, "period": r.period,
                    "predictions": r.predictions, "copilot_requests": r.copilot_requests,
                    "analytics_queries": r.analytics_queries, "realtime_events": r.realtime_events,
                    "storage_bytes": r.storage_bytes, "api_calls": r.api_calls,
                }
                if metric in data:
                    data[metric] = data[metric] + amount
                records[i] = TenantUsageRecord(**data)
                result = records[i]
                found = True
                break
        if not found:
            data: dict[str, Any] = {
                "tenant_id": tenant_id, "period": period,
                "predictions": 0, "copilot_requests": 0,
                "analytics_queries": 0, "realtime_events": 0,
                "storage_bytes": 0, "api_calls": 0,
            }
            if metric in data:
                data[metric] = amount
            result = TenantUsageRecord(**data)
            records.append(result)
        self._write_json(self.usage_file, [
            {
                "tenant_id": r.tenant_id, "period": r.period,
                "predictions": r.predictions, "copilot_requests": r.copilot_requests,
                "analytics_queries": r.analytics_queries, "realtime_events": r.realtime_events,
                "storage_bytes": r.storage_bytes, "api_calls": r.api_calls,
            }
            for r in records
        ])
        assert result is not None
        return result
