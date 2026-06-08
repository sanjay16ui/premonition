"""Audit compliance framework — HIPAA-minded audit trail helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class AuditEvent:
    actor: str
    action: str
    resource: str
    outcome: str
    timestamp: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class ComplianceAuditLogger:
    """Structured audit events for security and MLOps actions."""

    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def log(
        self,
        actor: str,
        action: str,
        resource: str,
        outcome: str = "success",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor=actor,
            action=action,
            resource=resource,
            outcome=outcome,
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=details or {},
        )
        self.events.append(event)
        return event

    def query(self, action: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        events = self.events
        if action:
            events = [e for e in events if e.action == action]
        return [e.to_dict() for e in events[-limit:]]
