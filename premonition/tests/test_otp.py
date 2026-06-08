"""Tests for OTP login endpoints.

Tests:
    - request-otp: valid email, rate limiting, lockout check
    - verify-otp: correct code, wrong code, expired, lockout, JWT issued
    - resend-otp: invalidates old OTP, issues new one

Uses TestClient to avoid async issues, and patches the email service so
no real emails are sent during testing.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure JWT is enabled for tests
os.environ.setdefault("PREMONITION_JWT_SECRET", "test-secret-for-otp-tests-32chars!")

from premonition.api.main import create_app  # noqa: E402
from premonition.auth.otp_store import OTPStore, _hash_otp  # noqa: E402


# ─────────────────────────────── Fixtures ───────────────────────────────────

@pytest.fixture()
def tmp_otp_store(tmp_path: Path) -> OTPStore:
    """Isolated OTPStore backed by a temp directory."""
    return OTPStore(tmp_path)


@pytest.fixture()
def app(tmp_path: Path):
    """App with mocked email service and fresh OTP store."""
    application = create_app()

    # Attach a fresh OTP store
    otp_store = OTPStore(tmp_path)
    application.state.otp_store = otp_store

    # Patch email service to never send real emails
    mock_email_svc = MagicMock()
    mock_email_svc.send_otp_email = AsyncMock(return_value=True)
    mock_email_svc._dev_mode = True
    application.state.email_service = mock_email_svc

    return application


@pytest.fixture()
def client(app):
    """Synchronous test client for the app."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def otp_store(app) -> OTPStore:
    return app.state.otp_store


# ─────────────────────────── Unit: OTPStore ──────────────────────────────────

class TestOTPStore:
    def test_create_otp_returns_4_digit_string(self, tmp_otp_store: OTPStore):
        otp, expires = tmp_otp_store.create_otp("doctor@hospital.com")
        assert len(otp) == 4
        assert otp.isdigit()
        assert expires == 120

    def test_otp_is_hashed_not_stored_in_plaintext(self, tmp_otp_store: OTPStore):
        otp, _ = tmp_otp_store.create_otp("doctor@hospital.com")
        record = tmp_otp_store.get_record("doctor@hospital.com")
        assert record is not None
        assert record.otp_hash != otp  # plaintext never stored
        # Verify hash is correct
        assert record.otp_hash == _hash_otp(otp, record.salt)

    def test_verify_correct_otp(self, tmp_otp_store: OTPStore):
        otp, _ = tmp_otp_store.create_otp("doc@hospital.com")
        success, msg = tmp_otp_store.verify_otp("doc@hospital.com", otp)
        assert success is True
        assert "success" in msg.lower()

    def test_verify_wrong_otp_increments_attempts(self, tmp_otp_store: OTPStore):
        tmp_otp_store.create_otp("doc@hospital.com")
        success, msg = tmp_otp_store.verify_otp("doc@hospital.com", "0000")
        assert success is False
        assert "2 attempt" in msg

    def test_lockout_after_3_wrong_attempts(self, tmp_otp_store: OTPStore):
        tmp_otp_store.create_otp("doc@hospital.com")
        for _ in range(3):
            tmp_otp_store.verify_otp("doc@hospital.com", "0000")
        locked, secs = tmp_otp_store.is_locked("doc@hospital.com")
        assert locked is True
        assert secs > 0

    def test_verify_returns_locked_message_after_lockout(self, tmp_otp_store: OTPStore):
        tmp_otp_store.create_otp("doc@hospital.com")
        for _ in range(2):
            tmp_otp_store.verify_otp("doc@hospital.com", "0000")
        # 3rd attempt triggers lockout
        success, msg = tmp_otp_store.verify_otp("doc@hospital.com", "0000")
        assert success is False
        assert "locked" in msg.lower()

    def test_otp_deleted_after_successful_verify(self, tmp_otp_store: OTPStore):
        otp, _ = tmp_otp_store.create_otp("doc@hospital.com")
        tmp_otp_store.verify_otp("doc@hospital.com", otp)
        record = tmp_otp_store.get_record("doc@hospital.com")
        assert record is None  # one-time use

    def test_verify_expired_otp(self, tmp_otp_store: OTPStore):
        otp, _ = tmp_otp_store.create_otp("doc@hospital.com")
        record = tmp_otp_store.get_record("doc@hospital.com")
        # Manually expire the record
        record.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        tmp_otp_store._set_record(record)
        success, msg = tmp_otp_store.verify_otp("doc@hospital.com", otp)
        assert success is False
        assert "expired" in msg.lower()

    def test_invalidate_removes_record(self, tmp_otp_store: OTPStore):
        tmp_otp_store.create_otp("doc@hospital.com")
        tmp_otp_store.invalidate_otp("doc@hospital.com")
        assert tmp_otp_store.get_record("doc@hospital.com") is None

    def test_resend_invalidates_old_otp(self, tmp_otp_store: OTPStore):
        old_otp, _ = tmp_otp_store.create_otp("doc@hospital.com")
        tmp_otp_store.invalidate_otp("doc@hospital.com")
        new_otp, _ = tmp_otp_store.create_otp("doc@hospital.com")
        # Old OTP no longer valid
        success, _ = tmp_otp_store.verify_otp("doc@hospital.com", old_otp)
        # new_otp may accidentally equal old_otp (rare), skip assertion in that case
        if old_otp != new_otp:
            assert success is False

    def test_rate_limit_after_5_requests(self, tmp_otp_store: OTPStore):
        """5 requests within 1 hour should block a 6th request."""
        email = "ratelimit@hospital.com"
        # Create OTP and immediately invalidate (simulates resend flow)
        # But do NOT reset the hour window — the window counter stays
        for i in range(5):
            tmp_otp_store.create_otp(email)
            # Manually expire so we can create again, but keep the hour window
            record = tmp_otp_store.get_record(email)
            if record:
                record.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
                tmp_otp_store._set_record(record)
        # 6th request should hit rate limit
        with pytest.raises(ValueError, match="Too many"):
            tmp_otp_store.create_otp(email)

    def test_case_insensitive_email(self, tmp_otp_store: OTPStore):
        otp, _ = tmp_otp_store.create_otp("DOCTOR@Hospital.COM")
        success, _ = tmp_otp_store.verify_otp("doctor@hospital.com", otp)
        assert success is True


# ──────────────────────────── API: request-otp ───────────────────────────────

class TestRequestOTP:
    def test_request_otp_any_email_returns_200(self, client: TestClient):
        res = client.post("/api/v1/auth/request-otp", json={"email": "anyone@example.com"})
        assert res.status_code == 200
        body = res.json()
        assert "expires_in_seconds" in body
        assert body["expires_in_seconds"] == 120
        assert "masked_email" in body
        # OTP must NOT be in response
        assert "otp" not in body
        assert "code" not in body

    def test_request_otp_masks_email(self, client: TestClient):
        res = client.post("/api/v1/auth/request-otp", json={"email": "doctor@hospital.org"})
        assert res.status_code == 200
        masked = res.json()["masked_email"]
        assert "doctor" not in masked  # local part is masked
        assert "@hospital.org" in masked

    def test_request_otp_invalid_email_returns_422(self, client: TestClient):
        res = client.post("/api/v1/auth/request-otp", json={"email": "not-an-email"})
        assert res.status_code == 422

    def test_request_otp_locked_returns_423(self, client: TestClient, otp_store: OTPStore):
        email = "locked@hospital.com"
        # Force lockout via 3 failed verify attempts
        otp_store.create_otp(email)
        for _ in range(3):
            otp_store.verify_otp(email, "0000")
        # Now the API endpoint should return 423 (not raise PermissionError)
        res = client.post("/api/v1/auth/request-otp", json={"email": email})
        assert res.status_code == 423


# ──────────────────────────── API: verify-otp ────────────────────────────────

class TestVerifyOTP:
    def test_verify_correct_code_returns_tokens(self, client: TestClient, otp_store: OTPStore):
        email = "verified@hospital.com"
        otp, _ = otp_store.create_otp(email)
        res = client.post("/api/v1/auth/verify-otp", json={"email": email, "code": otp})
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert "role" in body
        assert body["message"] == "Login successful."

    def test_verify_wrong_code_returns_401(self, client: TestClient, otp_store: OTPStore):
        email = "wrong@hospital.com"
        otp_store.create_otp(email)
        res = client.post("/api/v1/auth/verify-otp", json={"email": email, "code": "0000"})
        assert res.status_code == 401

    def test_verify_expired_code_returns_410(self, client: TestClient, otp_store: OTPStore):
        email = "expired@hospital.com"
        otp_store.create_otp(email)
        # Manually expire
        record = otp_store.get_record(email)
        record.expires_at = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
        otp_store._set_record(record)
        res = client.post("/api/v1/auth/verify-otp", json={"email": email, "code": "1234"})
        assert res.status_code == 410

    def test_verify_3_failures_locks_account(self, client: TestClient, otp_store: OTPStore):
        email = "lockme@hospital.com"
        otp_store.create_otp(email)
        for _ in range(3):
            client.post("/api/v1/auth/verify-otp", json={"email": email, "code": "0000"})
        # After 3 failures the store should report locked
        locked, _ = otp_store.is_locked(email)
        assert locked is True
        # And a 4th verify attempt must return 423
        res = client.post("/api/v1/auth/verify-otp", json={"email": email, "code": "0000"})
        assert res.status_code == 423

    def test_verify_no_otp_request_returns_401(self, client: TestClient):
        res = client.post("/api/v1/auth/verify-otp", json={"email": "ghost@hospital.com", "code": "1234"})
        assert res.status_code == 401

    def test_verify_non_numeric_code_returns_422(self, client: TestClient):
        res = client.post("/api/v1/auth/verify-otp", json={"email": "doc@hospital.com", "code": "ABCD"})
        assert res.status_code == 422

    def test_verify_code_too_short_returns_422(self, client: TestClient):
        res = client.post("/api/v1/auth/verify-otp", json={"email": "doc@hospital.com", "code": "123"})
        assert res.status_code == 422

    def test_otp_not_returned_in_request_response(self, client: TestClient):
        """Security: OTP numeric value must never appear as a JSON field in the response."""
        import json
        res = client.post("/api/v1/auth/request-otp", json={"email": "sec@hospital.com"})
        assert res.status_code == 200
        body = res.json()
        # JSON keys must not expose the actual OTP
        assert "otp" not in body
        assert "otp_hash" not in body
        assert "code" not in body          # no field named 'code'
        assert "salt" not in body
        # expires_in_seconds and masked_email are expected — not the OTP itself
        assert "expires_in_seconds" in body
        assert "masked_email" in body


# ──────────────────────────── API: resend-otp ────────────────────────────────

class TestResendOTP:
    def test_resend_returns_200(self, client: TestClient, otp_store: OTPStore):
        email = "resend@hospital.com"
        otp_store.create_otp(email)
        res = client.post("/api/v1/auth/resend-otp", json={"email": email})
        assert res.status_code == 200
        body = res.json()
        assert "New verification code sent" in body["message"]
        assert body["expires_in_seconds"] == 120

    def test_resend_invalidates_old_otp(self, client: TestClient, otp_store: OTPStore):
        email = "resend2@hospital.com"
        old_otp, _ = otp_store.create_otp(email)
        client.post("/api/v1/auth/resend-otp", json={"email": email})
        # Old OTP should no longer work
        res = client.post("/api/v1/auth/verify-otp", json={"email": email, "code": old_otp})
        # Either 401 (wrong code) or 410 (expired) — not 200
        assert res.status_code in (401, 410)

    def test_resend_locked_returns_423(self, client: TestClient, otp_store: OTPStore):
        email = "lockedresend@hospital.com"
        otp_store.create_otp(email)
        for _ in range(3):
            otp_store.verify_otp(email, "0000")
        # API should catch the lockout and return 423
        res = client.post("/api/v1/auth/resend-otp", json={"email": email})
        assert res.status_code == 423

    def test_resend_without_prior_request_still_works(self, client: TestClient):
        """Resend with no prior OTP should still issue a fresh OTP."""
        res = client.post("/api/v1/auth/resend-otp", json={"email": "fresh@hospital.com"})
        assert res.status_code == 200
