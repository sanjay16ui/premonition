"""Copilot RBAC enforcement tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from premonition.api.version import API_PREFIX

COPILOT = f"{API_PREFIX}/copilot"
JWT_SECRET = "copilot-rbac-test-secret-key-32bytes!"


@pytest.fixture
def jwt_client(monkeypatch, tmp_path):
    monkeypatch.setenv("PREMONITION_JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("PREMONITION_LOGS_DIR", str(tmp_path / "logs"))
    from premonition.auth import dependencies as auth_deps
    auth_deps._user_store = None
    from premonition.api.main import create_app
    with TestClient(create_app()) as client:
        yield client


def _token(client, email, password):
    return client.post(f"{API_PREFIX}/auth/login", json={"email": email, "password": password}).json()["access_token"]


class TestCopilotRBAC:
    def test_clinician_can_chat(self, jwt_client):
        token = _token(jwt_client, "clinician@premonition.health", "Clinician123!")
        resp = jwt_client.post(f"{COPILOT}/chat", json={"message": "hello"},
                               headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_auditor_cannot_chat(self, jwt_client):
        token = _token(jwt_client, "auditor@premonition.health", "Auditor123!")
        resp = jwt_client.post(f"{COPILOT}/chat", json={"message": "hello"},
                               headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_auditor_can_list_conversations(self, jwt_client):
        token = _token(jwt_client, "auditor@premonition.health", "Auditor123!")
        resp = jwt_client.get(f"{COPILOT}/conversations", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_executive_can_executive_summary(self, jwt_client):
        token = _token(jwt_client, "executive@premonition.health", "Executive123!")
        resp = jwt_client.post(f"{COPILOT}/executive-summary", json={},
                               headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_clinician_cannot_executive_summary(self, jwt_client):
        token = _token(jwt_client, "clinician@premonition.health", "Clinician123!")
        resp = jwt_client.post(f"{COPILOT}/executive-summary", json={},
                               headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_admin_can_ingest(self, jwt_client):
        token = _token(jwt_client, "admin@premonition.health", "AdminPass123!")
        resp = jwt_client.post(f"{COPILOT}/ingest-document", json={
            "title": "SOP", "content": "Protocol text here for testing ingestion.",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_executive_cannot_ingest(self, jwt_client):
        token = _token(jwt_client, "executive@premonition.health", "Executive123!")
        resp = jwt_client.post(f"{COPILOT}/ingest-document", json={
            "title": "SOP", "content": "Protocol text.",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_copilot_permissions_in_roles(self):
        from premonition.auth.roles import Role, has_permission
        assert has_permission(Role.CLINICIAN, "copilot:use")
        assert has_permission(Role.AUDITOR, "copilot:read")
        assert not has_permission(Role.AUDITOR, "copilot:use")
        assert has_permission(Role.EXECUTIVE, "copilot:executive")
