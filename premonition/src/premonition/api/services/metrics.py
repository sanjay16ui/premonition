"""Metrics service — operational metrics for monitoring."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from premonition.api.schemas.responses import MetricsResponse
from premonition.api.services.model_loader import ModelLoaderService


@dataclass
class MetricsCollector:
    """In-memory operational metrics (Prometheus-compatible export)."""

    start_time: float = field(default_factory=time.time)
    predictions_total: int = 0
    predictions_sepsis_alerts: int = 0
    predictions_errors: int = 0
    latency_samples_ms: list[float] = field(default_factory=list)
    last_prediction_at: str | None = None

    def record_prediction(self, prediction_label: str, latency_ms: float) -> None:
        self.predictions_total += 1
        if prediction_label == "sepsis_alert":
            self.predictions_sepsis_alerts += 1
        self.latency_samples_ms.append(latency_ms)
        if len(self.latency_samples_ms) > 1000:
            self.latency_samples_ms = self.latency_samples_ms[-500:]
        self.last_prediction_at = datetime.now(timezone.utc).isoformat()

    def record_error(self) -> None:
        self.predictions_errors += 1

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def avg_latency_ms(self) -> float:
        if not self.latency_samples_ms:
            return 0.0
        return sum(self.latency_samples_ms) / len(self.latency_samples_ms)


class MetricsService:
    """Expose JSON and Prometheus metrics."""

    def __init__(self, model_loader: ModelLoaderService, collector: MetricsCollector) -> None:
        self.model_loader = model_loader
        self.collector = collector

    def get_json_metrics(self) -> MetricsResponse:
        return MetricsResponse(
            predictions_total=self.collector.predictions_total,
            predictions_sepsis_alerts=self.collector.predictions_sepsis_alerts,
            predictions_errors=self.collector.predictions_errors,
            model_loaded=1 if self.model_loader.is_ready() else 0,
            uptime_seconds=round(self.collector.uptime_seconds, 2),
            avg_latency_ms=round(self.collector.avg_latency_ms, 2),
        )

    def get_prometheus_metrics(self) -> str:
        c = self.collector
        lines = [
            "# HELP premonition_predictions_total Total predictions served",
            "# TYPE premonition_predictions_total counter",
            f"premonition_predictions_total {c.predictions_total}",
            "# HELP premonition_sepsis_alerts_total Total sepsis alerts",
            "# TYPE premonition_sepsis_alerts_total counter",
            f"premonition_sepsis_alerts_total {c.predictions_sepsis_alerts}",
            "# HELP premonition_prediction_errors_total Total prediction errors",
            "# TYPE premonition_prediction_errors_total counter",
            f"premonition_prediction_errors_total {c.predictions_errors}",
            "# HELP premonition_model_loaded Whether model is loaded (1=yes)",
            "# TYPE premonition_model_loaded gauge",
            f"premonition_model_loaded {1 if self.model_loader.is_ready() else 0}",
            "# HELP premonition_uptime_seconds API uptime",
            "# TYPE premonition_uptime_seconds gauge",
            f"premonition_uptime_seconds {c.uptime_seconds:.2f}",
            "# HELP premonition_avg_latency_ms Average prediction latency",
            "# TYPE premonition_avg_latency_ms gauge",
            f"premonition_avg_latency_ms {c.avg_latency_ms:.2f}",
        ]
        return "\n".join(lines) + "\n"
