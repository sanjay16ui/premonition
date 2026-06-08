"""Executive intelligence service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from premonition.analytics.schemas import ExecutiveAnalytics


class ExecutiveIntelligenceService:
    """Generate executive dashboard intelligence."""

    def build(
        self,
        realtime_summary: dict[str, Any] | None,
        prediction_logs: list[dict[str, Any]],
        model_metrics: dict[str, Any],
        metrics_collector: dict[str, Any],
    ) -> ExecutiveAnalytics:
        rt = realtime_summary or {}
        preds_today = len(prediction_logs)
        alerts = rt.get("alerts_today", 0)
        high_risk = rt.get("high_risk_count", 0)
        avg_risk = rt.get("average_risk_score", 0.0)

        test_metrics = model_metrics.get("test", model_metrics)
        pr_auc = float(test_metrics.get("pr_auc", 0))

        return ExecutiveAnalytics(
            kpis={
                "icu_patients": rt.get("current_icu_patients", 0),
                "predictions_today": preds_today,
                "alerts_today": alerts,
                "high_risk_patients": high_risk,
                "average_risk_score": avg_risk,
                "model_pr_auc": pr_auc,
                "system_uptime_hours": round(metrics_collector.get("uptime_seconds", 0) / 3600, 2),
            },
            alerts_summary={
                "total": alerts,
                "critical": rt.get("critical_alert_count", 0),
                "black": rt.get("black_alert_count", 0),
                "trend": "stable",
            },
            risk_overview={
                "distribution": self._risk_distribution(prediction_logs),
                "top_critical": rt.get("top_critical", [])[:5],
            },
            model_performance={
                "model_name": test_metrics.get("model_name", "unknown"),
                "pr_auc": pr_auc,
                "recall": float(test_metrics.get("recall", 0)),
                "precision": float(test_metrics.get("precision", 0)),
            },
            operational_status={
                "model_loaded": metrics_collector.get("model_loaded", 0) == 1,
                "predictions_total": metrics_collector.get("predictions_total", 0),
                "avg_latency_ms": metrics_collector.get("avg_latency_ms", 0),
                "errors": metrics_collector.get("predictions_errors", 0),
            },
        )

    def _risk_distribution(self, logs: list[dict[str, Any]]) -> dict[str, int]:
        dist = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
        for log in logs:
            score = float(log.get("risk_score", 0))
            if score < 0.15:
                dist["low"] += 1
            elif score < 0.35:
                dist["moderate"] += 1
            elif score < 0.55:
                dist["high"] += 1
            else:
                dist["critical"] += 1
        return dist

    @staticmethod
    def load_model_metrics(models_dir: Path, tier: str) -> dict[str, Any]:
        path = models_dir / tier / "best_model" / "metrics.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
