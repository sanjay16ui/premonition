"""End-to-end workflow tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


class TestE2EWorkflows:
    def test_e2e_hospital_onboarding(self, client: TestClient):
        uid = uuid.uuid4().hex[:8]
        steps = []
        steps.append(client.post("/api/v1/organizations", json={
            "name": "E2E Health", "slug": f"e2e-health-{uid}", "contact_email": "e2e@test.com",
        }))
        assert steps[-1].status_code == 200
        org_id = steps[-1].json()["id"]

        steps.append(client.post("/api/v1/tenants", json={
            "hospital_name": "E2E Hospital", "slug": f"e2e-hospital-{uid}",
            "organization_id": org_id, "bed_capacity": 300, "icu_beds": 60,
        }))
        assert steps[-1].status_code == 200
        tenant_id = steps[-1].json()["id"]

        steps.append(client.patch(f"/api/v1/tenants/{tenant_id}/config", json={
            "config": {"realtime_enabled": True, "copilot_enabled": True},
        }))
        assert steps[-1].status_code == 200

        steps.append(client.post(f"/api/v1/tenants/{tenant_id}/members", json={
            "email": "clinician@e2e.com", "role": "clinician", "tenant_id": tenant_id,
        }))
        assert steps[-1].status_code == 200

        steps.append(client.get(f"/api/v1/tenants/{tenant_id}/billing"))
        assert steps[-1].status_code == 200

    def test_e2e_clinician_workflow(self, client: TestClient, sample_patient_features):
        predict = client.post("/api/v1/predict", json={
            "patient_id": "e2e-patient", "features": sample_patient_features,
        })
        assert predict.status_code == 200
        risk = predict.json().get("risk_score", 0)

        explain = client.post("/api/v1/explain", json={
            "patient_id": "e2e-patient", "features": sample_patient_features,
        })
        assert explain.status_code == 200

        if risk > 0.5:
            alert_exp = client.post("/api/v1/copilot/explain-alert", json={
                "alert_level": "RED", "risk_score": risk, "patient_id": "e2e-patient",
            })
            assert alert_exp.status_code == 200

        handover = client.post("/api/v1/copilot/handover", json={"patient_ids": ["e2e-patient"]})
        assert handover.status_code == 200

    def test_e2e_executive_workflow(self, client: TestClient):
        kpi = client.get("/api/v1/analytics/kpis")
        assert kpi.status_code == 200
        capacity = client.get("/api/v1/analytics/capacity")
        assert capacity.status_code == 200
        exec_summary = client.post("/api/v1/copilot/executive-summary", json={})
        assert exec_summary.status_code == 200

    def test_e2e_copilot_conversation(self, client: TestClient):
        chat1 = client.post("/api/v1/copilot/chat", json={"message": "Explain sepsis risk factors"})
        assert chat1.status_code == 200
        conv_id = chat1.json()["conversation_id"]

        chat2 = client.post("/api/v1/copilot/chat", json={
            "message": "What about lactate?", "conversation_id": conv_id,
        })
        assert chat2.status_code == 200

        convs = client.get("/api/v1/copilot/conversations")
        assert convs.status_code == 200

        detail = client.get(f"/api/v1/copilot/conversations/{conv_id}")
        assert detail.status_code == 200

    def test_e2e_document_ingest_and_search(self, client: TestClient):
        ingest = client.post("/api/v1/copilot/ingest-document", json={
            "title": "E2E Protocol", "content": "Sepsis protocol: measure lactate within 1 hour.",
            "source_type": "protocol",
        })
        assert ingest.status_code == 200

        search = client.post("/api/v1/copilot/search", json={"query": "lactate sepsis"})
        assert search.status_code == 200
        assert "citations" in search.json()
