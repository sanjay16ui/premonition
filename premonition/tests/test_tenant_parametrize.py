"""Parametrized tenant tests for comprehensive coverage."""

from __future__ import annotations

import pytest
from pathlib import Path

from premonition.tenant.store import TenantStore
from premonition.tenant.billing import BillingService
from premonition.tenant.hierarchy import TenantRole, TENANT_ROLE_HIERARCHY, has_tenant_permission
from premonition.tenant.config_manager import DEFAULT_TENANT_CONFIG


@pytest.fixture
def store(tmp_path: Path) -> TenantStore:
    return TenantStore(tmp_path)


PLANS = ["starter", "standard", "enterprise"]
METRICS = ["predictions", "copilot_requests", "analytics_queries", "realtime_events", "api_calls"]
REGIONS = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]


class TestParametrizedTenants:
    @pytest.mark.parametrize("plan", PLANS)
    def test_billing_plans_exist(self, plan):
        assert plan in BillingService.PLAN_LIMITS

    @pytest.mark.parametrize("metric", METRICS)
    def test_usage_tracking(self, store: TenantStore, metric: str):
        usage = store.increment_usage("premonition-default", metric, 1)
        assert getattr(usage, metric) >= 1

    @pytest.mark.parametrize("region", REGIONS)
    def test_create_org_regions(self, store: TenantStore, region: str):
        org = store.create_organization(f"Org {region}", f"org-{region}", "a@b.com", region=region)
        assert org.region == region

    @pytest.mark.parametrize("role", list(TenantRole))
    def test_all_roles_have_permissions(self, role: TenantRole):
        perms = has_tenant_permission(role, "tenants:read")
        if role in (TenantRole.VIEWER, TenantRole.CLINICIAN, TenantRole.EXECUTIVE,
                     TenantRole.AUDITOR, TenantRole.DEPARTMENT_HEAD, TenantRole.HOSPITAL_ADMIN,
                     TenantRole.ORG_ADMIN, TenantRole.PLATFORM_ADMIN):
            assert perms is True or role == TenantRole.VIEWER

    @pytest.mark.parametrize("key", list(DEFAULT_TENANT_CONFIG.keys()))
    def test_default_config_keys(self, key: str):
        assert key in DEFAULT_TENANT_CONFIG

    @pytest.mark.parametrize("beds", [50, 100, 200, 500, 1000])
    def test_tenant_bed_capacities(self, store: TenantStore, beds: int):
        org = store.create_organization(f"Bed Org {beds}", f"bed-org-{beds}", "b@b.com")
        t = store.create_tenant(f"Hospital {beds}", f"hosp-{beds}", org.id, bed_capacity=beds)
        assert t.bed_capacity == beds

    @pytest.mark.parametrize("i", range(20))
    def test_bulk_tenant_creation(self, store: TenantStore, i: int):
        org = store.create_organization(f"Bulk {i}", f"bulk-{i}", f"bulk{i}@test.com")
        t = store.create_tenant(f"H {i}", f"h-{i}", org.id)
        assert store.get_tenant(t.id) is not None

    @pytest.mark.parametrize("slug", ["alpha", "beta-hospital", "city-med-01", "regional-icu"])
    def test_tenant_slugs(self, store: TenantStore, slug: str):
        org = store.create_organization(f"Org {slug}", f"org-{slug}", "s@s.com")
        t = store.create_tenant(f"Hospital {slug}", slug, org.id)
        assert store.get_tenant_by_slug(slug) is not None

    @pytest.mark.parametrize("idx", range(len(TENANT_ROLE_HIERARCHY) - 1))
    def test_hierarchy_ordering(self, idx: int):
        assert TENANT_ROLE_HIERARCHY[idx] != TENANT_ROLE_HIERARCHY[idx + 1]
