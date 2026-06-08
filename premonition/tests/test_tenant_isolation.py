"""Strict tenant isolation tests — row-level security."""

from __future__ import annotations

import pytest
from pathlib import Path

from premonition.tenant.context import TenantContext, set_tenant_context, clear_tenant_context
from premonition.tenant.isolation import assert_tenant_access, filter_by_tenant, stamp_tenant, tenant_subdir, TenantIsolationError
from premonition.tenant.service import TenantService
from premonition.tenant.onboarding import TenantOnboardingService
from premonition.tenant.store import TenantStore


@pytest.fixture
def multi_tenant_setup(tmp_path: Path):
    store = TenantStore(tmp_path)
    onboarding = TenantOnboardingService(store, tmp_path)
    t1 = onboarding.onboard(
        org_name="Org A", org_slug="org-a", org_email="a@a.com",
        hospital_name="Hospital A", tenant_slug="hospital-a", admin_email="a@hospital.com",
    )
    t2 = onboarding.onboard(
        org_name="Org B", org_slug="org-b", org_email="b@b.com",
        hospital_name="Hospital B", tenant_slug="hospital-b", admin_email="b@hospital.com",
    )
    return store, t1["tenant"].id, t2["tenant"].id, tmp_path


class TestStrictIsolation:
    def test_separate_data_directories(self, multi_tenant_setup):
        _, tid_a, tid_b, logs_dir = multi_tenant_setup
        dir_a = tenant_subdir(logs_dir, "audit", tid_a)
        dir_b = tenant_subdir(logs_dir, "audit", tid_b)
        assert dir_a != dir_b
        assert tid_a in str(dir_a)
        assert tid_b in str(dir_b)

    def test_rls_filter_blocks_cross_tenant(self, multi_tenant_setup):
        _, tid_a, tid_b, _ = multi_tenant_setup
        records = [
            {"id": 1, "tenant_id": tid_a, "data": "secret-a"},
            {"id": 2, "tenant_id": tid_b, "data": "secret-b"},
        ]
        set_tenant_context(TenantContext(tid_a, "org-a", "hospital-a"))
        filtered = filter_by_tenant(records)
        assert len(filtered) == 1
        assert filtered[0]["data"] == "secret-a"
        clear_tenant_context()

    def test_cross_tenant_access_denied(self, multi_tenant_setup):
        _, tid_a, tid_b, _ = multi_tenant_setup
        ctx = TenantContext(tid_a, "org-a", "hospital-a")
        with pytest.raises(TenantIsolationError):
            assert_tenant_access(tid_b, ctx)

    def test_stamp_enforces_tenant_on_write(self, multi_tenant_setup):
        _, tid_a, _, _ = multi_tenant_setup
        set_tenant_context(TenantContext(tid_a, "org-a", "hospital-a"))
        record = stamp_tenant({"action": "predict", "patient_id": "p-1"})
        assert record["tenant_id"] == tid_a
        clear_tenant_context()

    def test_usage_tracked_per_tenant(self, multi_tenant_setup, tmp_path):
        _, tid_a, tid_b, _ = multi_tenant_setup
        svc = TenantService(tmp_path)
        svc.track_prediction(tid_a)
        svc.track_prediction(tid_a)
        svc.track_prediction(tid_b)
        usage_a = svc.usage.get_current_usage(tid_a)
        usage_b = svc.usage.get_current_usage(tid_b)
        assert usage_a.predictions >= 2
        assert usage_b.predictions >= 1

    @pytest.mark.parametrize("subdir", ["audit", "copilot/conversations", "models", "realtime", "analytics"])
    def test_provisioned_subdirs_exist(self, multi_tenant_setup, subdir):
        _, tid_a, _, logs_dir = multi_tenant_setup
        path = tenant_subdir(logs_dir, subdir, tid_a)
        assert path.exists()

    def test_tenant_configs_independent(self, multi_tenant_setup, tmp_path):
        _, tid_a, tid_b, _ = multi_tenant_setup
        svc = TenantService(tmp_path)
        svc.config.update_config(tid_a, {"max_patients_monitored": 25})
        svc.config.update_config(tid_b, {"max_patients_monitored": 75})
        assert svc.config.get_config(tid_a)["max_patients_monitored"] == 25
        assert svc.config.get_config(tid_b)["max_patients_monitored"] == 75
