"""Alerting system — threshold-based alerts for drift and performance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    name: str
    severity: AlertSeverity
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class AlertManager:
    """In-memory alert store with Prometheus-compatible counter export."""

    def __init__(self) -> None:
        self.alerts: list[Alert] = []
        self._fired_counts: dict[str, int] = {}

    def fire(self, alert: Alert) -> None:
        self.alerts.append(alert)
        self._fired_counts[alert.name] = self._fired_counts.get(alert.name, 0) + 1
        if len(self.alerts) > 500:
            self.alerts = self.alerts[-250:]

    def check_drift_alert(self, drift_score: float, threshold: float = 0.2) -> Alert | None:
        if drift_score > threshold:
            alert = Alert(
                name="data_drift",
                severity=AlertSeverity.WARNING if drift_score < 0.5 else AlertSeverity.CRITICAL,
                message=f"Data drift PSI {drift_score:.3f} exceeds threshold {threshold}",
                metadata={"psi": drift_score, "threshold": threshold},
            )
            self.fire(alert)
            return alert
        return None

    def check_latency_alert(self, latency_ms: float, threshold_ms: float = 2000) -> Alert | None:
        if latency_ms > threshold_ms:
            alert = Alert(
                name="high_latency",
                severity=AlertSeverity.WARNING,
                message=f"Prediction latency {latency_ms:.0f}ms exceeds {threshold_ms}ms",
                metadata={"latency_ms": latency_ms},
            )
            self.fire(alert)
            return alert
        return None

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.alerts[-limit:]]

    def prometheus_lines(self) -> str:
        lines = [
            "# HELP premonition_alerts_fired_total Alerts fired by name",
            "# TYPE premonition_alerts_fired_total counter",
        ]
        for name, count in self._fired_counts.items():
            lines.append(f'premonition_alerts_fired_total{{alert="{name}"}} {count}')
        return "\n".join(lines) + "\n"
