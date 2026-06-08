"""Authentication tests — JWT, login, refresh, API keys."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

JWT_SECRET = "test-jwt-secret-for-section-10"


@pytest.fixture
def jwt_env(monkeypatch, tmp_path):
    monkeypatch.setenv("PREMONITION_JWT_SECRET", JWT_SECRET)
    monkeypatch.setenv("PREMONITION_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.delenv("PREMONITION_API_KEY", raising=False)
    from premonition.auth import dependencies as auth_deps
    auth_deps._user_store = None
    from premonition.api.main import create_app
    with TestClient(create_app()) as client:
        yield client


def test_login_success(jwt_env):
    resp = jwt_env.post("/api/v1/auth/login", json={
        "email": "admin@premonition.health",
        "password": "AdminPass123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "admin"


def test_login_invalid_credentials(jwt_env):
    resp = jwt_env.post("/api/v1/auth/login", json={
        "email": "admin@premonition.health",
        "password": "wrong-password",
    })
    assert resp.status_code == 401


def test_refresh_token(jwt_env):
    login = jwt_env.post("/api/v1/auth/login", json={
        "email": "clinician@premonition.health",
        "password": "Clinician123!",
    }).json()
    resp = jwt_env.post("/api/v1/auth/refresh", json={
        "refresh_token": login["refresh_token"],
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_me_endpoint(jwt_env):
    login = jwt_env.post("/api/v1/auth/login", json={
        "email": "auditor@premonition.health",
        "password": "Auditor123!",
    }).json()
    resp = jwt_env.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "auditor"


def test_jwt_required_when_configured(jwt_env):
    resp = jwt_env.get("/api/v1/system/status")
    assert resp.status_code == 401


def test_jwt_access_grants_api(jwt_env):
    login = jwt_env.post("/api/v1/auth/login", json={
        "email": "clinician@premonition.health",
        "password": "Clinician123!",
    }).json()
    resp = jwt_env.get(
        "/api/v1/system/status",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert resp.status_code == 200


def test_create_api_key_admin(jwt_env):
    login = jwt_env.post("/api/v1/auth/login", json={
        "email": "admin@premonition.health",
        "password": "AdminPass123!",
    }).json()
    resp = jwt_env.post(
        "/api/v1/auth/api-keys",
        json={"name": "ci-bot", "role": "clinician"},
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["key"].startswith("pmk_")


def test_login_disabled_without_jwt_secret(client, monkeypatch):
    monkeypatch.delenv("PREMONITION_JWT_SECRET", raising=False)
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@premonition.health",
        "password": "AdminPass123!",
    })
    assert resp.status_code == 503
