"""RBAC tests — role permissions and access control."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from premonition.auth.roles import Role, has_permission


@pytest.fixture
def jwt_clients(monkeypatch, tmp_path):
    monkeypatch.setenv("PREMONITION_JWT_SECRET", "rbac-test-secret")
    monkeypatch.setenv("PREMONITION_LOGS_DIR", str(tmp_path / "logs"))
    from premonition.auth import dependencies as auth_deps
    auth_deps._user_store = None
    from premonition.api.main import create_app

    users = {
        "admin": ("admin@premonition.health", "AdminPass123!"),
        "clinician": ("clinician@premonition.health", "Clinician123!"),
        "executive": ("executive@premonition.health", "Executive123!"),
        "auditor": ("auditor@premonition.health", "Auditor123!"),
    }
    tokens = {}
    with TestClient(create_app()) as client:
        for role, (email, password) in users.items():
            resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
            tokens[role] = resp.json()["access_token"]
        yield client, tokens


def test_admin_has_mlops_permission():
    assert has_permission(Role.ADMIN, "mlops:manage")


def test_auditor_cannot_predict():
    assert not has_permission(Role.AUDITOR, "predict")


def test_clinician_can_predict():
    assert has_permission(Role.CLINICIAN, "predict")


def test_executive_can_read_realtime_executive():
    assert has_permission(Role.EXECUTIVE, "realtime:executive")


def test_auditor_denied_mlops(jwt_clients):
    client, tokens = jwt_clients
    resp = client.get(
        "/api/v1/mlops/status",
        headers={"Authorization": f"Bearer {tokens['auditor']}"},
    )
    assert resp.status_code == 403


def test_admin_can_access_mlops(jwt_clients):
    client, tokens = jwt_clients
    resp = client.get(
        "/api/v1/mlops/status",
        headers={"Authorization": f"Bearer {tokens['admin']}"},
    )
    assert resp.status_code == 200


def test_clinician_denied_mlops_manage(jwt_clients):
    client, tokens = jwt_clients
    resp = client.post(
        "/api/v1/mlops/promote/staging",
        headers={"Authorization": f"Bearer {tokens['clinician']}"},
    )
    assert resp.status_code == 403


def test_executive_can_read_metrics(jwt_clients):
    client, tokens = jwt_clients
    resp = client.get(
        "/api/v1/metrics",
        headers={"Authorization": f"Bearer {tokens['executive']}"},
    )
    assert resp.status_code == 200
