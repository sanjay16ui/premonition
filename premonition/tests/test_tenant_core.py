"""Tests for multi-tenant core modules."""

from __future__ import annotations

import pytest
from pathlib import Path

from premonition.tenant.context import TenantContext, get_default_tenant_id, set_tenant_context, clear_tenant_context
from premonition.tenant.isolation import assert_tenant_access, filter_by_tenant, stamp_tenant, tenant_root, TenantIsolationError
from premonition.tenant.store import TenantStore
from premonition.tenant.billing import BillingService
from premonition.tenant.usage import UsageTracker
from premonition.tenant.config_manager import TenantConfigManager
from premonition.tenant.hierarchy import TenantRole, has_tenant_permission, can_manage_tenant, map_platform_role_to_tenant
from premonition.tenant.onboarding import TenantOnboardingService
from premonition.tenant.service import TenantService
from premonition.auth.roles import Role


@pytest.fixture
def tenant_store(tmp_path: Path) -> TenantStore:
    return TenantStore(tmp_path)


@pytest.fixture
def tenant_service(tmp_path: Path) -> TenantService:
    return TenantService(tmp_path)


class TestTenantContext:
    def test_default_tenant_id(self):
        assert get_default_tenant_id() == "premonition-default"

    def test_set_and_get_context(self):
        ctx = TenantContext(tenant_id="t-1", organization_id="o-1", slug="hospital-a")
        set_tenant_context(ctx)
        from premonition.tenant.context import get_tenant_context
        assert get_tenant_context().tenant_id == "t-1"
        clear_tenant_context()

    def test_is_default(self):
        ctx = TenantContext(tenant_id="premonition-default", organization_id="o", slug="default")
        assert ctx.is_default is True


class TestTenantStore:
    def test_default_tenant_exists(self, tenant_store: TenantStore):
        tenants = tenant_store.list_tenants()
        assert len(tenants) >= 1
        assert tenants[0].id == "premonition-default"

    def test_create_organization(self, tenant_store: TenantStore):
        org = tenant_store.create_organization("Test Org", "test-org", "admin@test.com")
        assert org.slug == "test-org"
        assert tenant_store.get_organization(org.id) is not None

    def test_create_tenant(self, tenant_store: TenantStore):
        org = tenant_store.create_organization("Org2", "org2", "a@b.com")
        tenant = tenant_store.create_tenant("Hospital B", "hospital-b", org.id)
        assert tenant.slug == "hospital-b"
        assert tenant.organization_id == org.id

    def test_get_tenant_by_slug(self, tenant_store: TenantStore):
        t = tenant_store.get_tenant_by_slug("default")
        assert t is not None

    def test_update_config(self, tenant_store: TenantStore):
        updated = tenant_store.update_tenant_config("premonition-default", {"custom_flag": True})
        assert updated is not None
        assert updated.config.get("custom_flag") is True

    def test_deactivate_tenant(self, tenant_store: TenantStore):
        org = tenant_store.create_organization("Org3", "org3", "x@y.com")
        t = tenant_store.create_tenant("H3", "h3", org.id)
        deactivated = tenant_store.deactivate_tenant(t.id)
        assert deactivated.status == "inactive"

    def test_add_member(self, tenant_store: TenantStore):
        m = tenant_store.add_member("user@test.com", "clinician", "premonition-default")
        assert m.email == "user@test.com"

    def test_increment_usage(self, tenant_store: TenantStore):
        usage = tenant_store.increment_usage("premonition-default", "predictions", 5)
        assert usage.predictions >= 5

    def test_billing_plan(self, tenant_store: TenantStore):
        plan = tenant_store.get_billing("premonition-default")
        assert plan is not None
        assert plan.plan in ("standard", "enterprise")


class TestTenantIsolation:
    def test_stamp_tenant(self):
        set_tenant_context(TenantContext("t-1", "o-1", "slug"))
        record = stamp_tenant({"action": "predict"})
        assert record["tenant_id"] == "t-1"
        clear_tenant_context()

    def test_filter_by_tenant(self):
        records = [
            {"id": 1, "tenant_id": "t-1"},
            {"id": 2, "tenant_id": "t-2"},
            {"id": 3, "tenant_id": "t-1"},
        ]
        set_tenant_context(TenantContext("t-1", "o-1", "s"))
        filtered = filter_by_tenant(records)
        assert len(filtered) == 2
        clear_tenant_context()

    def test_assert_tenant_access_passes(self):
        ctx = TenantContext("t-1", "o-1", "s")
        assert_tenant_access("t-1", ctx)

    def test_assert_tenant_access_fails(self):
        ctx = TenantContext("t-1", "o-1", "s")
        with pytest.raises(TenantIsolationError):
            assert_tenant_access("t-2", ctx)

    def test_tenant_root(self, tmp_path: Path):
        root = tenant_root(tmp_path, "t-abc")
        assert "tenants" in str(root)
        assert root.exists()


class TestBilling:
    def test_check_limit_within(self, tenant_store: TenantStore):
        billing = BillingService(tenant_store)
        assert billing.check_limit("premonition-default", "predictions") is True

    def test_estimate_cost(self, tenant_store: TenantStore):
        billing = BillingService(tenant_store)
        cost = billing.estimate_cost("premonition-default")
        assert "estimated_total" in cost
        assert cost["base_monthly"] > 0


class TestUsageTracker:
    def test_track_metric(self, tenant_store: TenantStore):
        tracker = UsageTracker(tenant_store)
        usage = tracker.track("premonition-default", "api_calls", 3)
        assert usage.api_calls >= 3

    def test_unknown_metric_raises(self, tenant_store: TenantStore):
        tracker = UsageTracker(tenant_store)
        with pytest.raises(ValueError):
            tracker.track("premonition-default", "invalid_metric")


class TestConfigManager:
    def test_get_config(self, tenant_store: TenantStore):
        mgr = TenantConfigManager(tenant_store)
        config = mgr.get_config("premonition-default")
        assert config["model_tier"] == "t1"

    def test_is_feature_enabled(self, tenant_store: TenantStore):
        mgr = TenantConfigManager(tenant_store)
        assert mgr.is_feature_enabled("premonition-default", "shap_explainability") is True


class TestHierarchy:
    @pytest.mark.parametrize("role,perm,expected", [
        (TenantRole.PLATFORM_ADMIN, "tenants:manage", True),
        (TenantRole.VIEWER, "tenants:manage", False),
        (TenantRole.CLINICIAN, "predict", True),
        (TenantRole.AUDITOR, "audit:read", True),
        (TenantRole.EXECUTIVE, "copilot:executive", True),
    ])
    def test_tenant_permissions(self, role, perm, expected):
        assert has_tenant_permission(role, perm) == expected

    def test_can_manage_tenant(self):
        assert can_manage_tenant(TenantRole.PLATFORM_ADMIN, TenantRole.CLINICIAN) is True
        assert can_manage_tenant(TenantRole.VIEWER, TenantRole.CLINICIAN) is False

    def test_map_platform_role(self):
        assert map_platform_role_to_tenant(Role.ADMIN) == TenantRole.HOSPITAL_ADMIN


class TestOnboarding:
    def test_onboard_hospital(self, tmp_path: Path, tenant_store: TenantStore):
        onboarding = TenantOnboardingService(tenant_store, tmp_path)
        result = onboarding.onboard(
            org_name="New Health", org_slug="new-health",
            org_email="admin@new.com", hospital_name="City Hospital",
            tenant_slug="city-hospital", admin_email="admin@city.com",
        )
        assert result["tenant"].slug == "city-hospital"
        assert len(result["provisioned_paths"]) > 0

    def test_duplicate_slug_raises(self, tmp_path: Path, tenant_store: TenantStore):
        onboarding = TenantOnboardingService(tenant_store, tmp_path)
        onboarding.onboard(
            org_name="A", org_slug="a-org", org_email="a@a.com",
            hospital_name="H", tenant_slug="dup", admin_email="x@x.com",
        )
        with pytest.raises(ValueError):
            onboarding.onboard(
                org_name="B", org_slug="b-org", org_email="b@b.com",
                hospital_name="H2", tenant_slug="dup", admin_email="y@y.com",
            )


class TestTenantService:
    def test_resolve_context_default(self, tenant_service: TenantService):
        ctx = tenant_service.resolve_context()
        assert ctx.tenant_id == "premonition-default"

    def test_track_api_call(self, tenant_service: TenantService):
        tenant_service.track_api_call("premonition-default")
        usage = tenant_service.usage.get_current_usage("premonition-default")
        assert usage.api_calls >= 1
