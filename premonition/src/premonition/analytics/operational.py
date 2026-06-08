"""Operational analytics service."""

from __future__ import annotations

from typing import Any


class OperationalAnalyticsService:
    """Hospital operational intelligence reporting."""

    def report(
        self,
        prediction_logs: list[dict[str, Any]],
        alert_logs: list[dict[str, Any]],
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        pred_by_hour = self._hourly_counts(prediction_logs)
        alert_by_level = self._alert_breakdown(alert_logs)
        sepsis_alerts = sum(1 for p in prediction_logs if p.get("prediction") == 1)

        return {
            "predictions": {
                "total": len(prediction_logs),
                "sepsis_alerts": sepsis_alerts,
                "alert_rate": round(sepsis_alerts / max(len(prediction_logs), 1), 4),
                "hourly_trend": pred_by_hour,
            },
            "alerts": {
                "total": len(alert_logs),
                "by_level": alert_by_level,
            },
            "performance": {
                "avg_latency_ms": metrics.get("avg_latency_ms", 0),
                "error_rate": round(
                    metrics.get("predictions_errors", 0) / max(metrics.get("predictions_total", 1), 1), 4,
                ),
                "uptime_seconds": metrics.get("uptime_seconds", 0),
            },
            "trends": {
                "prediction_volume": "increasing" if len(pred_by_hour) > 3 else "stable",
                "alert_severity": "elevated" if alert_by_level.get("RED", 0) + alert_by_level.get("BLACK", 0) > 2 else "normal",
            },
        }

    def _hourly_counts(self, logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        hours: dict[str, int] = {}
        for log in logs:
            ts = log.get("timestamp", "")
            hour = ts[11:13] if len(ts) >= 13 else "00"
            hours[hour] = hours.get(hour, 0) + 1
        return [{"hour": h, "count": c} for h, c in sorted(hours.items())]

    def _alert_breakdown(self, logs: list[dict[str, Any]]) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        for log in logs:
            level = str(log.get("level", log.get("alert_level", "UNKNOWN"))).upper()
            breakdown[level] = breakdown.get(level, 0) + 1
        return breakdown
