"""Alert prioritization AI."""

from __future__ import annotations

from typing import Any


class AlertPrioritizationAI:
    """Score and rank alerts by clinical urgency."""

    LEVEL_WEIGHTS = {
        "BLACK": 100, "RED": 80, "ORANGE": 60, "YELLOW": 40, "GREEN": 10,
    }

    def prioritize(self, alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        scored = []
        for alert in alerts:
            level = str(alert.get("level", alert.get("alert_level", "GREEN"))).upper()
            risk = float(alert.get("risk_score", 0))
            velocity = float(alert.get("risk_velocity", 0))
            score = self.LEVEL_WEIGHTS.get(level, 20) + risk * 50 + max(velocity, 0) * 30
            scored.append({**alert, "priority_score": round(score, 2), "level": level})

        scored.sort(key=lambda a: a["priority_score"], reverse=True)
        for i, alert in enumerate(scored):
            alert["priority_rank"] = i + 1
        return scored

    def top_critical(self, alerts: list[dict[str, Any]], n: int = 5) -> list[dict[str, Any]]:
        return self.prioritize(alerts)[:n]
