"""User and API key storage."""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from premonition.auth.password import hash_password, verify_password
from premonition.auth.roles import Role
from premonition.utils.paths import ensure_dir


@dataclass
class User:
    email: str
    password_hash: str
    role: Role
    active: bool = True


class UserStore:
    """File-backed user store with default seed users."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = ensure_dir(data_dir / "auth")
        self.users_file = self.data_dir / "users.json"
        self.api_keys_file = self.data_dir / "api_keys.json"
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if not self.users_file.exists():
            defaults = [
                User("admin@premonition.health", hash_password("AdminPass123!"), Role.ADMIN),
                User("clinician@premonition.health", hash_password("Clinician123!"), Role.CLINICIAN),
                User("executive@premonition.health", hash_password("Executive123!"), Role.EXECUTIVE),
                User("auditor@premonition.health", hash_password("Auditor123!"), Role.AUDITOR),
            ]
            self._save_users(defaults)

    def _load_users(self) -> list[User]:
        data = json.loads(self.users_file.read_text(encoding="utf-8"))
        return [
            User(
                email=u["email"],
                password_hash=u["password_hash"],
                role=Role(u["role"]),
                active=u.get("active", True),
            )
            for u in data
        ]

    def _save_users(self, users: list[User]) -> None:
        payload = [
            {
                "email": u.email,
                "password_hash": u.password_hash,
                "role": u.role.value,
                "active": u.active,
            }
            for u in users
        ]
        self.users_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def authenticate(self, email: str, password: str) -> User | None:
        for user in self._load_users():
            if user.email == email and user.active:
                if verify_password(password, user.password_hash):
                    return user
        return None

    def get_user(self, email: str) -> User | None:
        for user in self._load_users():
            if user.email == email:
                return user
        return None

    @staticmethod
    def _hash_api_key(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def create_api_key(self, name: str, role: Role) -> dict[str, Any]:
        key = f"pmk_{secrets.token_urlsafe(32)}"
        record = {
            "name": name,
            "key_hash": self._hash_api_key(key),
            "role": role.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "active": True,
        }
        keys = self._load_api_keys()
        keys.append(record)
        self.api_keys_file.write_text(json.dumps(keys, indent=2), encoding="utf-8")
        return {"name": name, "key": key, "role": role, "created_at": record["created_at"]}

    def _load_api_keys(self) -> list[dict[str, Any]]:
        if not self.api_keys_file.exists():
            return []
        return json.loads(self.api_keys_file.read_text(encoding="utf-8"))

    def verify_api_key(self, key: str) -> Role | None:
        key_hash = self._hash_api_key(key)
        for record in self._load_api_keys():
            if record.get("active") and record["key_hash"] == key_hash:
                return Role(record["role"])
        return None
