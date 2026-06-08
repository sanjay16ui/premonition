"""Realtime monitoring integration tests."""

from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def realtime_client():
    os.environ["PREMONITION_REALTIME_ENABLED"] = "true"
    from premonition.api.main import create_app
    with TestClient(create_app()) as c:
        yield c
    os.environ["PREMONITION_REALTIME_ENABLED"] = "false"


class TestRealtimeMonitoring:
    def test_realtime_status(self, client: TestClient):
        r = client.get("/api/v1/realtime/status")
        assert r.status_code == 200

    def test_realtime_patients(self, client: TestClient):
        r = client.get("/api/v1/realtime/patients")
        assert r.status_code == 200

    def test_realtime_alerts(self, client: TestClient):
        r = client.get("/api/v1/realtime/alerts")
        assert r.status_code == 200

    def test_realtime_notifications(self, client: TestClient):
        r = client.get("/api/v1/realtime/notifications")
        assert r.status_code == 200

    def test_sse_endpoint_exists(self, client: TestClient):
        from unittest.mock import patch
        async def mock_generator(*args, **kwargs):
            yield "event: connected\ndata: {\"status\": \"connected\"}\n\n"
        with patch("premonition.realtime.streaming.StreamingHub.sse_generator", side_effect=mock_generator):
            r = client.get("/api/v1/realtime/stream")
            assert r.status_code in (200, 503)

    def test_realtime_with_tenant(self, client: TestClient):
        r = client.get("/api/v1/realtime/patients", headers={"X-Tenant-ID": "premonition-default"})
        assert r.status_code == 200
