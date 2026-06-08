"""Tests for tenant management API endpoints."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


def _uid() -> str:
    return uuid.uuid4().hex[:8]


class TestTenantAPI:
    def test_list_tenants(self, client: TestClient):
        r = client.get("/api/v1/tenants")
        assert r.status_code == 200
        data = r.json()
        assert "count" in data
        assert data["count"] >= 1

    def test_get_default_tenant(self, client: TestClient):
        r = client.get("/api/v1/tenants/premonition-default")
        assert r.status_code == 200
        assert r.json()["slug"] == "default"

    def test_tenant_header_returned(self, client: TestClient):
        r = client.get("/api/v1/health")
        assert "X-Tenant-ID" in r.headers

    def test_custom_tenant_header(self, client: TestClient):
        r = client.get("/api/v1/health", headers={"X-Tenant-ID": "premonition-default"})
        assert r.headers["X-Tenant-ID"] == "premonition-default"

    def test_list_organizations(self, client: TestClient):
        r = client.get("/api/v1/organizations")
        assert r.status_code == 200
        assert r.json()["count"] >= 1

    def test_get_organization(self, client: TestClient):
        r = client.get("/api/v1/organizations/org-default")
        assert r.status_code == 200
        assert r.json()["slug"] == "premonition"

    def test_get_usage(self, client: TestClient):
        r = client.get("/api/v1/tenants/premonition-default/usage")
        assert r.status_code == 200
        assert "api_calls" in r.json()

    def test_get_billing(self, client: TestClient):
        r = client.get("/api/v1/tenants/premonition-default/billing")
        assert r.status_code == 200
        assert "plan" in r.json()

    def test_billing_estimate(self, client: TestClient):
        r = client.get("/api/v1/tenants/premonition-default/billing/estimate")
        assert r.status_code == 200
        assert "estimated_total" in r.json()

    def test_create_organization(self, client: TestClient):
        r = client.post("/api/v1/organizations", json={
            "name": "Test Health System", "slug": "test-health-sys",
            "contact_email": "admin@testhealth.com", "region": "us-west-2", "plan": "standard",
        })
        assert r.status_code == 200
        assert r.json()["slug"] == "test-health-sys"

    def test_create_tenant(self, client: TestClient):
        org_r = client.post("/api/v1/organizations", json={
            "name": "Org For Tenant", "slug": "org-for-tenant",
            "contact_email": "o@t.com",
        })
        org_id = org_r.json()["id"]
        r = client.post("/api/v1/tenants", json={
            "hospital_name": "Regional Medical", "slug": "regional-med",
            "organization_id": org_id, "bed_capacity": 200, "icu_beds": 40,
        })
        assert r.status_code == 200
        assert r.json()["hospital_name"] == "Regional Medical"

    def test_onboard_tenant(self, client: TestClient):
        uid = _uid()
        r = client.post("/api/v1/tenants/onboard", json={
            "organization": {
                "name": "Onboard Org", "slug": f"onboard-org-{uid}",
                "contact_email": "onboard@test.com",
            },
            "tenant": {
                "hospital_name": "Onboard Hospital", "slug": f"onboard-hosp-{uid}",
                "organization_id": "placeholder", "bed_capacity": 150, "icu_beds": 30,
            },
            "admin_email": "admin@onboard.com",
            "admin_role": "admin",
        })
        assert r.status_code == 200
        assert "tenant" in r.json()

    def test_update_config(self, client: TestClient):
        r = client.patch("/api/v1/tenants/premonition-default/config", json={
            "config": {"max_patients_monitored": 100},
        })
        assert r.status_code == 200

    def test_add_member(self, client: TestClient):
        r = client.post("/api/v1/tenants/premonition-default/members", json={
            "email": "newclinician@test.com", "role": "clinician", "tenant_id": "premonition-default",
        })
        assert r.status_code == 200

    def test_tenant_not_found(self, client: TestClient):
        r = client.get("/api/v1/tenants/nonexistent-tenant-id")
        assert r.status_code == 404

    def test_deactivate_tenant(self, client: TestClient):
        uid = _uid()
        org_r = client.post("/api/v1/organizations", json={
            "name": "Deact Org", "slug": f"deact-org-{uid}", "contact_email": "d@d.com",
        })
        t_r = client.post("/api/v1/tenants", json={
            "hospital_name": "Deact Hosp", "slug": f"deact-hosp-{uid}",
            "organization_id": org_r.json()["id"],
        })
        tid = t_r.json()["id"]
        r = client.delete(f"/api/v1/tenants/{tid}")
        assert r.status_code == 200
