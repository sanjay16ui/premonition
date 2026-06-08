"""Load and stress tests."""

from __future__ import annotations

import concurrent.futures
import time

import pytest
from fastapi.testclient import TestClient


class TestLoadStress:
    def test_concurrent_health_checks(self, client: TestClient):
        def hit():
            return client.get("/api/v1/health").status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(lambda _: hit(), range(50)))
        assert all(r == 200 for r in results)

    def test_concurrent_tenant_requests(self, client: TestClient):
        def hit(i):
            return client.get("/api/v1/tenants", headers={"X-Tenant-ID": "premonition-default"}).status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(hit, range(30)))
        assert all(r == 200 for r in results)

    def test_rapid_copilot_requests(self, client: TestClient):
        statuses = []
        for i in range(10):
            r = client.post("/api/v1/copilot/chat", json={"message": f"Quick question {i}"})
            statuses.append(r.status_code)
        assert all(s == 200 for s in statuses)

    def test_health_response_time(self, client: TestClient):
        start = time.perf_counter()
        client.get("/api/v1/health")
        elapsed = time.perf_counter() - start
        assert elapsed < 2.0

    def test_tenant_list_response_time(self, client: TestClient):
        start = time.perf_counter()
        client.get("/api/v1/tenants")
        elapsed = time.perf_counter() - start
        assert elapsed < 3.0

    @pytest.mark.parametrize("n", [5, 10, 15])
    def test_batch_predictions(self, client: TestClient, sample_patient_features, n):
        statuses = []
        for i in range(n):
            r = client.post("/api/v1/predict", json={
                "patient_id": f"load-p-{i}", "features": sample_patient_features,
            })
            statuses.append(r.status_code)
        assert sum(1 for s in statuses if s == 200) >= n - 1
