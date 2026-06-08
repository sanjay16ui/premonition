"""Copilot API endpoint tests."""

from __future__ import annotations

import pytest

from premonition.api.version import API_PREFIX

COPILOT = f"{API_PREFIX}/copilot"


class TestCopilotChat:
    def test_chat_endpoint(self, client):
        resp = client.post(f"{COPILOT}/chat", json={"message": "What is sepsis?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "conversation_id" in data

    def test_chat_returns_citations(self, client):
        resp = client.post(f"{COPILOT}/chat", json={"message": "Explain Sepsis-3 criteria"})
        assert resp.status_code == 200
        assert "citations" in resp.json()


class TestCopilotExplain:
    def test_explain_prediction(self, client):
        resp = client.post(f"{COPILOT}/explain-prediction", json={
            "risk_score": 0.72, "prediction_label": "sepsis_alert",
            "top_factors": ["hr_mean", "spo2_mean"],
        })
        assert resp.status_code == 200
        assert len(resp.json()["message"]) > 10

    def test_explain_alert(self, client):
        resp = client.post(f"{COPILOT}/explain-alert", json={
            "alert_level": "RED", "risk_score": 0.85, "top_factors": ["hypoxemia"],
        })
        assert resp.status_code == 200


class TestCopilotSummaries:
    def test_patient_summary(self, client):
        resp = client.post(f"{COPILOT}/patient-summary", json={"patient_id": "patient-001"})
        assert resp.status_code == 200

    def test_handover(self, client):
        resp = client.post(f"{COPILOT}/handover", json={"patient_ids": ["p1", "p2"]})
        assert resp.status_code == 200

    def test_executive_summary(self, client):
        resp = client.post(f"{COPILOT}/executive-summary", json={"include_kpis": True})
        assert resp.status_code == 200

    def test_recommendations(self, client):
        resp = client.post(f"{COPILOT}/recommendations", json={"risk_score": 0.65})
        assert resp.status_code == 200


class TestCopilotRAG:
    def test_ingest_document(self, client):
        resp = client.post(f"{COPILOT}/ingest-document", json={
            "title": "Test Protocol",
            "content": "All sepsis patients require lactate measurement within 1 hour.",
            "doc_type": "protocol",
        })
        assert resp.status_code == 200
        assert resp.json()["chunks"] >= 1

    def test_search(self, client):
        resp = client.post(f"{COPILOT}/search", json={"query": "sepsis lactate", "top_k": 3})
        assert resp.status_code == 200
        assert "citations" in resp.json()


class TestCopilotConversations:
    def test_list_conversations(self, client):
        client.post(f"{COPILOT}/chat", json={"message": "Hello copilot"})
        resp = client.get(f"{COPILOT}/conversations")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_conversation(self, client):
        chat = client.post(f"{COPILOT}/chat", json={"message": "Test conv"}).json()
        resp = client.get(f"{COPILOT}/conversations/{chat['conversation_id']}")
        assert resp.status_code == 200
        assert len(resp.json()["messages"]) >= 2

    def test_get_missing_conversation(self, client):
        resp = client.get(f"{COPILOT}/conversations/nonexistent-id")
        assert resp.status_code == 404


class TestCopilotMemory:
    def test_conversation_persistence(self, client):
        r1 = client.post(f"{COPILOT}/chat", json={"message": "First message"}).json()
        r2 = client.post(f"{COPILOT}/chat", json={
            "message": "Follow up", "conversation_id": r1["conversation_id"],
        })
        assert r2.status_code == 200
        detail = client.get(f"{COPILOT}/conversations/{r1['conversation_id']}").json()
        assert len(detail["messages"]) == 4
