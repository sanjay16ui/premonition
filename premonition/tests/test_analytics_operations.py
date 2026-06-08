"""KPI engine, executive intelligence, operational analytics tests."""

from __future__ import annotations

import pytest

from premonition.analytics.executive import ExecutiveIntelligenceService
from premonition.analytics.kpis import HospitalKPIEngine
from premonition.analytics.operational import OperationalAnalyticsService
from premonition.analytics.service import AnalyticsService


class TestHospitalKPIs:
    def test_compute_kpis(self, settings):
        engine = HospitalKPIEngine()
        metrics = HospitalKPIEngine.load_metrics(settings.models_dir, settings.primary_tier)
        result = engine.compute(
            prediction_logs=[{"risk_score": 0.4, "prediction": 1}, {"risk_score": 0.1, "prediction": 0}],
            model_metrics=metrics,
            metrics_collector={"predictions_total": 10, "predictions_errors": 0, "uptime_seconds": 3600},
        )
        assert result.sepsis_detection_rate > 0
        assert result.predictions_per_day == 2

    def test_uptime_calculation(self, settings):
        engine = HospitalKPIEngine()
        result = engine.compute([], {}, {"predictions_total": 100, "predictions_errors": 5})
        assert result.model_uptime_pct == 95.0

    def test_avg_risk_score(self, settings):
        engine = HospitalKPIEngine()
        logs = [{"risk_score": 0.2}, {"risk_score": 0.6}]
        result = engine.compute(logs, {}, {})
        assert result.avg_risk_score == 0.4


class TestExecutiveIntelligence:
    def test_build_executive_analytics(self, settings):
        svc = ExecutiveIntelligenceService()
        metrics = svc.load_model_metrics(settings.models_dir, settings.primary_tier)
        result = svc.build(
            realtime_summary={"current_icu_patients": 10, "high_risk_count": 3, "alerts_today": 5},
            prediction_logs=[{"risk_score": 0.5, "prediction": 1}],
            model_metrics=metrics,
            metrics_collector={"uptime_seconds": 7200, "predictions_total": 50},
        )
        assert result.kpis["icu_patients"] == 10
        assert "pr_auc" in str(result.model_performance)

    def test_risk_distribution_from_logs(self):
        svc = ExecutiveIntelligenceService()
        logs = [{"risk_score": 0.1}, {"risk_score": 0.4}, {"risk_score": 0.7}]
        dist = svc._risk_distribution(logs)
        assert sum(dist.values()) == 3


class TestOperationalAnalytics:
    def test_operational_report(self):
        svc = OperationalAnalyticsService()
        report = svc.report(
            prediction_logs=[
                {"timestamp": "2026-06-05T10:00:00", "prediction": 1, "risk_score": 0.6},
                {"timestamp": "2026-06-05T11:00:00", "prediction": 0, "risk_score": 0.2},
            ],
            alert_logs=[{"level": "RED"}, {"level": "YELLOW"}],
            metrics={"avg_latency_ms": 45, "predictions_total": 100, "predictions_errors": 2, "uptime_seconds": 5000},
        )
        assert report["predictions"]["total"] == 2
        assert report["alerts"]["by_level"]["RED"] == 1

    def test_hourly_trend(self):
        svc = OperationalAnalyticsService()
        logs = [{"timestamp": f"2026-06-05T{h:02d}:00:00", "prediction": 0} for h in range(5)]
        report = svc.report(logs, [], {})
        assert len(report["predictions"]["hourly_trend"]) >= 1


class TestAnalyticsService:
    def test_service_initializes(self, settings):
        svc = AnalyticsService(settings)
        assert svc.ensemble is not None
        assert svc.kpis is not None

    def test_get_population(self, settings):
        svc = AnalyticsService(settings)
        result = svc.get_population()
        assert result["total_patients"] > 0

    def test_compare_models(self, settings):
        svc = AnalyticsService(settings)
        result = svc.compare_models()
        assert "winner" in result

    def test_risk_stratification_fallback(self, settings):
        svc = AnalyticsService(settings)
        result = svc.risk_stratification()
        assert result["total_patients"] > 0

    def test_simulate_icu_surge(self, settings):
        svc = AnalyticsService(settings)
        result = svc.simulate(__import__("premonition.analytics.schemas", fromlist=["SimulateRequest"]).SimulateRequest(
            scenario="icu_surge", parameters={"patients": 18, "beds": 20},
        ))
        assert "current_occupancy" in result

    def test_get_kpis(self, settings):
        svc = AnalyticsService(settings)
        result = svc.get_kpis()
        assert "sepsis_detection_rate" in result

    def test_cohort_analysis(self, settings):
        from premonition.analytics.schemas import CohortAnalysisRequest
        svc = AnalyticsService(settings)
        result = svc.cohort_analysis(CohortAnalysisRequest(segment_by="age_group"))
        assert len(result) >= 1

    def test_get_benchmarks(self, settings):
        svc = AnalyticsService(settings)
        result = svc.get_benchmarks()
        assert "winner" in result
