"""Performance benchmark tests."""

from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from premonition.tenant.store import TenantStore
from premonition.tenant.service import TenantService


class TestPerformance:
    def test_tenant_store_list_performance(self, tmp_path):
        store = TenantStore(tmp_path)
        for i in range(50):
            org = store.create_organization(f"Org {i}", f"org-{i}", f"admin{i}@test.com")
            store.create_tenant(f"Hospital {i}", f"hospital-{i}", org.id)

        start = time.perf_counter()
        tenants = store.list_tenants()
        elapsed = time.perf_counter() - start
        assert len(tenants) >= 51
        assert elapsed < 1.0

    def test_usage_increment_performance(self, tmp_path):
        svc = TenantService(tmp_path)
        start = time.perf_counter()
        for _ in range(100):
            svc.track_api_call("premonition-default")
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0

    def test_api_health_latency(self, client: TestClient):
        times = []
        for _ in range(10):
            start = time.perf_counter()
            client.get("/api/v1/health")
            times.append(time.perf_counter() - start)
        avg = sum(times) / len(times)
        assert avg < 0.5

    def test_tenant_resolve_performance(self, tmp_path):
        svc = TenantService(tmp_path)
        start = time.perf_counter()
        for _ in range(200):
            svc.resolve_context()
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0
