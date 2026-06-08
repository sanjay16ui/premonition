"""API analytics service wrapper."""

from __future__ import annotations

from typing import Any

from fastapi import Request

from premonition.analytics.schemas import (
    CohortAnalysisRequest,
    OutcomePredictionRequest,
    RecommendationRequest,
    RiskStratificationRequest,
    SimulateRequest,
)
from premonition.analytics.service import AnalyticsService


class AnalyticsApiService:
    """Thin wrapper exposing AnalyticsService to API routes."""

    def __init__(self, analytics: AnalyticsService, request: Request | None = None) -> None:
        self.analytics = analytics
        self._request = request

    def _metrics_collector(self) -> dict[str, Any]:
        if self._request is None:
            return {}
        collector = getattr(self._request.app.state, "metrics_collector", None)
        if collector is None:
            return {}
        return {
            "predictions_total": collector.predictions_total,
            "predictions_errors": collector.predictions_errors,
            "uptime_seconds": collector.uptime_seconds,
            "avg_latency_ms": collector.avg_latency_ms,
            "model_loaded": 1 if getattr(self._request.app.state.model_loader, "is_ready", lambda: False)() else 0,
        }

    def _realtime_summary(self) -> dict[str, Any] | None:
        if self._request is None:
            return None
        rt = getattr(self._request.app.state, "realtime_service", None)
        if rt is None:
            return None
        try:
            summary = rt.get_executive_summary()
            return summary.model_dump() if hasattr(summary, "model_dump") else summary
        except Exception:
            return None

    async def get_executive(self) -> dict:
        return self.analytics.get_executive(self._realtime_summary(), self._metrics_collector())

    async def get_population(self) -> dict:
        return self.analytics.get_population()

    async def get_cohorts(self, request: CohortAnalysisRequest | None = None) -> list[dict]:
        return self.analytics.get_cohorts(request)

    async def get_outcomes(self, request: OutcomePredictionRequest) -> list[dict]:
        return self.analytics.get_outcomes(request)

    async def get_capacity(self) -> dict:
        return self.analytics.get_capacity(self._realtime_summary())

    async def get_resources(self) -> dict:
        return self.analytics.get_resources(self._realtime_summary())

    async def get_kpis(self) -> dict:
        return self.analytics.get_kpis(self._metrics_collector())

    async def simulate(self, request: SimulateRequest) -> dict:
        return self.analytics.simulate(request)

    async def compare_models(self) -> dict:
        return self.analytics.compare_models()

    async def get_recommendations(self, request: RecommendationRequest) -> list[dict]:
        return self.analytics.get_recommendations(request)

    async def risk_stratification(self, request: RiskStratificationRequest | None = None) -> dict:
        return self.analytics.risk_stratification(request)

    async def cohort_analysis(self, request: CohortAnalysisRequest) -> list[dict]:
        return self.analytics.cohort_analysis(request)

    async def outcome_prediction(self, request: OutcomePredictionRequest) -> list[dict]:
        return self.analytics.outcome_prediction(request)
