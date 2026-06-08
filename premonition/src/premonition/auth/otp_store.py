"""OTP storage — file-backed, with hashing, expiry, attempt tracking, and lockout."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import secrets
import string
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from premonition.utils.paths import ensure_dir

_logger = logging.getLogger(__name__)

OTP_EXPIRY_SECONDS = 600          # 10 minutes (extended for email delivery latency)
OTP_MAX_ATTEMPTS = 3
OTP_LOCKOUT_HOURS = 2
OTP_RATE_LIMIT_PER_HOUR = 5      # max OTP requests per email per hour
OTP_DIGITS = 4


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_otp(otp: str, salt: str) -> str:
    """SHA-256 hash of OTP + salt. OTP is never stored in plaintext."""
    return hashlib.sha256(f"{salt}{otp}".encode("utf-8")).hexdigest()


@dataclass
class OTPRecord:
    email: str
    otp_hash: str
    salt: str
    created_at: str           # ISO-8601
    expires_at: str           # ISO-8601
    attempts: int = 0
    locked_until: str | None = None
    request_count_this_hour: int = 0
    hour_window_start: str | None = None  # ISO-8601

    def is_expired(self) -> bool:
        return _now() >= datetime.fromisoformat(self.expires_at)

    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return _now() < datetime.fromisoformat(self.locked_until)

    def lockout_remaining_seconds(self) -> int:
        if not self.locked_until:
            return 0
        remaining = datetime.fromisoformat(self.locked_until) - _now()
        return max(0, int(remaining.total_seconds()))

    def seconds_until_expiry(self) -> int:
        remaining = datetime.fromisoformat(self.expires_at) - _now()
        return max(0, int(remaining.total_seconds()))


class OTPStore:
    """File-backed OTP store. Thread-safe for single-process use."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = ensure_dir(data_dir / "auth")
        self.records_file = self.data_dir / "otp_records.json"

    # ------------------------------------------------------------------ I/O

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.records_file.exists():
            return {}
        try:
            return json.loads(self.records_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, records: dict[str, dict[str, Any]]) -> None:
        self.records_file.write_text(
            json.dumps(records, indent=2), encoding="utf-8"
        )

    def _get_record(self, email: str) -> OTPRecord | None:
        records = self._load()
        data = records.get(email.lower())
        if data is None:
            return None
        return OTPRecord(**data)

    def _set_record(self, record: OTPRecord) -> None:
        records = self._load()
        records[record.email.lower()] = asdict(record)
        self._save(records)

    def _delete_record(self, email: str) -> None:
        records = self._load()
        records.pop(email.lower(), None)
        self._save(records)

    # ------------------------------------------------------------ Rate limit

    def _check_rate_limit(self, email: str) -> tuple[bool, int]:
        """Returns (is_rate_limited, requests_this_hour)."""
        record = self._get_record(email)
        now = _now()
        if record is None:
            return False, 0
        window_start = (
            datetime.fromisoformat(record.hour_window_start)
            if record.hour_window_start
            else now - timedelta(hours=2)
        )
        if now - window_start >= timedelta(hours=1):
            # Window expired — reset
            return False, 0
        return record.request_count_this_hour >= OTP_RATE_LIMIT_PER_HOUR, record.request_count_this_hour

    # ---------------------------------------------------------- Public API

    def is_locked(self, email: str) -> tuple[bool, int]:
        """Returns (is_locked, seconds_remaining)."""
        record = self._get_record(email)
        if record is None:
            return False, 0
        return record.is_locked(), record.lockout_remaining_seconds()

    def create_otp(self, email: str) -> tuple[str, int]:
        """
        Generate a new OTP for the given email.
        Returns (plaintext_otp, expires_in_seconds).
        Raises ValueError on rate limit.
        Raises PermissionError if locked.
        """
        email = email.lower()

        # Check lockout first
        locked, secs = self.is_locked(email)
        if locked:
            raise PermissionError(f"Account locked for {secs} more seconds.")

        # Check rate limit
        rate_limited, count = self._check_rate_limit(email)
        if rate_limited:
            raise ValueError(f"Too many OTP requests. Try again in an hour.")

        _gen_start = time.perf_counter()
        otp = "".join(random.SystemRandom().choices(string.digits, k=OTP_DIGITS))
        _logger.debug("OTP generated for %s in %.4fs", email, time.perf_counter() - _gen_start)
        salt = secrets.token_hex(16)
        otp_hash = _hash_otp(otp, salt)
        now = _now()
        expires_at = now + timedelta(seconds=OTP_EXPIRY_SECONDS)

        # Preserve rate-limit window
        existing = self._get_record(email)
        if existing and existing.hour_window_start:
            window_start = existing.hour_window_start
            old_count = existing.request_count_this_hour
            # If window hasn't expired keep the counter
            if _now() - datetime.fromisoformat(window_start) < timedelta(hours=1):
                new_count = old_count + 1
            else:
                window_start = now.isoformat()
                new_count = 1
        else:
            window_start = now.isoformat()
            new_count = 1

        record = OTPRecord(
            email=email,
            otp_hash=otp_hash,
            salt=salt,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
            attempts=0,
            locked_until=None,
            request_count_this_hour=new_count,
            hour_window_start=window_start,
        )
        self._set_record(record)
        return otp, OTP_EXPIRY_SECONDS

    def verify_otp(self, email: str, code: str) -> tuple[bool, str]:
        """
        Verify submitted OTP code.
        Returns (success, message).
        On 3rd failure, locks the account.
        """
        email = email.lower()
        record = self._get_record(email)

        if record is None:
            return False, "No OTP found for this email. Please request one."

        if record.is_locked():
            secs = record.lockout_remaining_seconds()
            mins = secs // 60
            return False, f"Account locked. Try again in {mins} minute(s)."

        if record.is_expired():
            return False, "OTP has expired. Please request a new one."

        submitted_hash = _hash_otp(code.strip(), record.salt)
        if submitted_hash == record.otp_hash:
            # Valid — delete record (one-time use)
            self._delete_record(email)
            return True, "OTP verified successfully."

        # Wrong code — increment attempts
        record.attempts += 1
        if record.attempts >= OTP_MAX_ATTEMPTS:
            locked_until = _now() + timedelta(hours=OTP_LOCKOUT_HOURS)
            record.locked_until = locked_until.isoformat()
            self._set_record(record)
            return False, (
                f"Too many incorrect attempts. Account locked for {OTP_LOCKOUT_HOURS} hour(s)."
            )

        remaining = OTP_MAX_ATTEMPTS - record.attempts
        self._set_record(record)
        return False, f"Incorrect code. {remaining} attempt(s) remaining."

    def invalidate_otp(self, email: str) -> None:
        """Delete OTP record (used before issuing a resend)."""
        self._delete_record(email.lower())

    def get_record(self, email: str) -> OTPRecord | None:
        """Read-only access for route handlers."""
        return self._get_record(email.lower())

    def cleanup_expired(self) -> int:
        """Remove all fully-expired, unlocked records from disk. Returns count removed."""
        records = self._load()
        to_delete = [
            email for email, data in records.items()
            if OTPRecord(**data).is_expired() and not OTPRecord(**data).is_locked()
        ]
        for email in to_delete:
            records.pop(email)
        if to_delete:
            self._save(records)
            _logger.info("OTPStore cleanup: removed %d expired record(s)", len(to_delete))
        return len(to_delete)
