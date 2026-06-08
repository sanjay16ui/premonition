"""Feature and prediction monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class FeatureMonitor:
    """Track feature distributions over sliding window."""

    window_size: int = 500
    feature_samples: dict[str, list[float]] = field(default_factory=dict)

    def record(self, features: dict[str, float]) -> None:
        for name, value in features.items():
            if name not in self.feature_samples:
                self.feature_samples[name] = []
            self.feature_samples[name].append(float(value))
            if len(self.feature_samples[name]) > self.window_size:
                self.feature_samples[name] = self.feature_samples[name][-self.window_size:]

    def summary(self) -> dict[str, dict[str, float]]:
        result = {}
        for name, values in self.feature_samples.items():
            if values:
                result[name] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
        return result


@dataclass
class PredictionMonitor:
    """Track prediction score distribution and alert rate."""

    scores: list[float] = field(default_factory=list)
    alerts: int = 0
    total: int = 0
    window_size: int = 1000

    def record(self, score: float, is_alert: bool) -> None:
        self.total += 1
        if is_alert:
            self.alerts += 1
        self.scores.append(score)
        if len(self.scores) > self.window_size:
            self.scores = self.scores[-self.window_size:]

    def summary(self) -> dict[str, Any]:
        alert_rate = self.alerts / max(self.total, 1)
        mean_score = sum(self.scores) / len(self.scores) if self.scores else 0.0
        return {
            "total_predictions": self.total,
            "alert_count": self.alerts,
            "alert_rate": round(alert_rate, 4),
            "mean_score": round(mean_score, 4),
            "window_size": len(self.scores),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
