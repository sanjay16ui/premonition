"""Security middleware and hardening tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from premonition.auth.password import hash_password, verify_password
from premonition.ops.secrets import SecretRotationRegistry


def test_security_headers_present(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "Content-Security-Policy" in resp.headers


def test_password_hashing():
    hashed = hash_password("SecurePass123!")
    assert hashed != "SecurePass123!"
    assert verify_password("SecurePass123!", hashed)
    assert not verify_password("wrong", hashed)


def test_secret_rotation_validate(monkeypatch):
    monkeypatch.setenv("PREMONITION_JWT_SECRET", "current-secret")
    monkeypatch.setenv("PREMONITION_JWT_SECRET_PREVIOUS", "old-secret")
    registry = SecretRotationRegistry()
    assert registry.validate_any("premonition-jwt-secret", "current-secret")
    assert registry.validate_any("premonition-jwt-secret", "old-secret")
    assert not registry.validate_any("premonition-jwt-secret", "invalid")


def test_csrf_blocks_unauthenticated_mutations(monkeypatch, tmp_path):
    monkeypatch.setenv("PREMONITION_JWT_SECRET", "csrf-test-secret")
    monkeypatch.setenv("PREMONITION_LOGS_DIR", str(tmp_path / "logs"))
    from premonition.auth import dependencies as auth_deps
    auth_deps._user_store = None
    from premonition.api.main import create_app
    with TestClient(create_app()) as client:
        resp = client.post("/api/v1/mlops/drift/check", json={"reference_features": {}})
        assert resp.status_code == 403


def test_legacy_api_key_still_works(monkeypatch):
    monkeypatch.setenv("PREMONITION_API_KEY", "legacy-test-key")
    monkeypatch.delenv("PREMONITION_JWT_SECRET", raising=False)
    from premonition.auth import dependencies as auth_deps
    auth_deps._user_store = None
    from premonition.api.main import create_app
    with TestClient(create_app()) as client:
        resp = client.get("/api/v1/system/status", headers={"X-API-Key": "legacy-test-key"})
        assert resp.status_code == 200
