"""JWT access and refresh token management."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from premonition.auth.roles import Role

ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("PREMONITION_JWT_ACCESS_MINUTES", "30"))
REFRESH_TOKEN_DAYS = int(os.getenv("PREMONITION_JWT_REFRESH_DAYS", "7"))


def get_jwt_secret() -> str | None:
    return os.getenv("PREMONITION_JWT_SECRET") or None


def is_jwt_enabled() -> bool:
    return get_jwt_secret() is not None


def create_access_token(subject: str, role: Role, extra: dict[str, Any] | None = None) -> str:
    secret = get_jwt_secret()
    if not secret:
        raise RuntimeError("JWT secret not configured")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role.value,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "jti": str(uuid.uuid4()),
        **(extra or {}),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def create_refresh_token(subject: str, role: Role) -> str:
    secret = get_jwt_secret()
    if not secret:
        raise RuntimeError("JWT secret not configured")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role.value,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_DAYS),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, secret, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    secret = get_jwt_secret()
    if not secret:
        raise RuntimeError("JWT secret not configured")
    return jwt.decode(token, secret, algorithms=[ALGORITHM])
