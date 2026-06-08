"""Cross-module integration tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


class TestPlatformIntegration:
    def test_health_with_tenant(self, client: TestClient):
        r = client.get("/api/v1/health", headers={"X-Tenant-ID": "premonition-default"})
        assert r.status_code == 200

    def test_predict_with_tenant_tracking(self, client: TestClient, sample_patient_features):
        client.post("/api/v1/predict", json={
            "patient_id": "int-p-1", "features": sample_patient_features,
        }, headers={"X-Tenant-ID": "premonition-default"})
        usage = client.get("/api/v1/tenants/premonition-default/usage")
        assert usage.status_code == 200

    def test_copilot_with_tenant(self, client: TestClient):
        r = client.post("/api/v1/copilot/chat", json={"message": "What is Sepsis-3?"})
        assert r.status_code == 200
        assert "message" in r.json()

    def test_analytics_with_tenant(self, client: TestClient):
        r = client.get("/api/v1/analytics/executive")
        assert r.status_code == 200

    def test_realtime_status(self, client: TestClient):
        r = client.get("/api/v1/realtime/status")
        assert r.status_code == 200

    def test_audit_with_tenant(self, client: TestClient):
        r = client.get("/api/v1/audit/logs")
        assert r.status_code == 200

    def test_metrics_with_tenant(self, client: TestClient):
        r = client.get("/api/v1/metrics")
        assert r.status_code == 200

    def test_models_registry(self, client: TestClient):
        r = client.get("/api/v1/models/version")
        assert r.status_code == 200

    def test_system_info(self, client: TestClient):
        r = client.get("/api/v1/system/status")
        assert r.status_code == 200

    def test_full_clinical_flow(self, client: TestClient, sample_patient_features):
        predict = client.post("/api/v1/predict", json={
            "patient_id": "flow-p-1", "features": sample_patient_features,
        })
        assert predict.status_code == 200
        explain = client.post("/api/v1/explain", json={
            "patient_id": "flow-p-1", "features": sample_patient_features,
        })
        assert explain.status_code == 200
        summary = client.post("/api/v1/copilot/patient-summary", json={"patient_id": "flow-p-1"})
        assert summary.status_code == 200

    def test_executive_flow(self, client: TestClient):
        exec_r = client.get("/api/v1/analytics/executive")
        assert exec_r.status_code == 200
        copilot_exec = client.post("/api/v1/copilot/executive-summary", json={})
        assert copilot_exec.status_code == 200

    def test_tenant_onboard_then_use(self, client: TestClient, sample_patient_features):
        uid = uuid.uuid4().hex[:8]
        onboard = client.post("/api/v1/tenants/onboard", json={
            "organization": {"name": "Int Org", "slug": f"int-org-{uid}", "contact_email": "i@i.com"},
            "tenant": {"hospital_name": "Int Hosp", "slug": f"int-hosp-{uid}", "organization_id": "x", "bed_capacity": 50, "icu_beds": 10},
            "admin_email": "admin@int.com", "admin_role": "admin",
        })
        assert onboard.status_code == 200
        tenant_id = onboard.json()["tenant"]["id"]
        r = client.get(f"/api/v1/tenants/{tenant_id}", headers={"X-Tenant-ID": tenant_id})
        assert r.status_code == 200
