"""Secrets management and rotation support."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class SecretMetadata:
    name: str
    version: int
    rotated_at: str
    active: bool = True


class SecretRotationRegistry:
    """
    Track secret versions for rotation without downtime.

    Supports dual-key validation during rotation window.
    """

    def __init__(self) -> None:
        self._versions: dict[str, list[SecretMetadata]] = {}

    def register(self, name: str, version: int = 1) -> SecretMetadata:
        meta = SecretMetadata(
            name=name,
            version=version,
            rotated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._versions.setdefault(name, []).append(meta)
        return meta

    def get_active_secrets(self, name: str) -> list[str]:
        """Return env var values for active versions (current + previous during rotation)."""
        env_base = name.upper().replace("-", "_")
        current = os.getenv(env_base)
        previous = os.getenv(f"{env_base}_PREVIOUS")
        secrets = []
        if current:
            secrets.append(current)
        if previous:
            secrets.append(previous)
        return secrets

    def validate_any(self, name: str, candidate: str) -> bool:
        import secrets as sec
        return any(sec.compare_digest(candidate, s) for s in self.get_active_secrets(name))
