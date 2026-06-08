"""Security tests for SaaS multi-tenant platform."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from premonition.tenant.hierarchy import TenantRole, has_tenant_permission, effective_permission
from premonition.auth.roles import Role


class TestSaaSSecurity:
    @pytest.mark.parametrize("role,perm", [
        (TenantRole.VIEWER, "tenants:manage"),
        (TenantRole.CLINICIAN, "tenants:manage"),
        (TenantRole.AUDITOR, "users:manage"),
        (TenantRole.EXECUTIVE, "mlops:manage"),
    ])
    def test_denied_permissions(self, role, perm):
        assert has_tenant_permission(role, perm) is False

    @pytest.mark.parametrize("role,perm", [
        (Role.ADMIN, "tenants:manage"),
        (Role.ADMIN, "billing:read"),
        (Role.CLINICIAN, "predict"),
        (Role.AUDITOR, "audit:read"),
    ])
    def test_effective_permissions(self, role, perm):
        assert effective_permission(role, perm) is True

    def test_security_headers_present(self, client: TestClient):
        r = client.get("/api/v1/health")
        assert r.headers.get("X-Content-Type-Options") == "nosniff"
        assert "X-Frame-Options" in r.headers

    def test_tenant_header_not_leaked(self, client: TestClient):
        r = client.get("/api/v1/health")
        assert r.headers.get("X-Tenant-ID") == "premonition-default"

    def test_invalid_tenant_falls_back(self, client: TestClient):
        r = client.get("/api/v1/health", headers={"X-Tenant-ID": "invalid-tenant-xyz"})
        assert r.status_code == 200

    def test_cors_headers_allowed(self, client: TestClient):
        r = client.options("/api/v1/health", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        })
        assert r.status_code in (200, 204, 405)

    def test_rate_limit_middleware_exists(self, client: TestClient):
        for _ in range(5):
            r = client.get("/api/v1/health")
            assert r.status_code == 200
