"""Outcome prediction and capacity/resource analytics tests."""

from __future__ import annotations

import pytest

from premonition.analytics.capacity import CapacityPlanningAnalytics
from premonition.analytics.outcomes import OutcomePredictionFramework
from premonition.analytics.resources import ResourceUtilizationAnalytics
from premonition.analytics.schemas import OutcomePredictionRequest


class TestOutcomePrediction:
    def test_predict_24h_outcomes(self):
        framework = OutcomePredictionFramework()
        results = framework.predict(
            OutcomePredictionRequest(horizon_hours=24),
            risk_score=0.5,
            features={"hr_mean": 100, "spo2_mean": 94, "comorbidity_count": 2},
        )
        assert len(results) >= 2
        assert all(0 <= r.probability <= 1 for r in results)

    def test_high_risk_elevated_sepsis_prob(self):
        framework = OutcomePredictionFramework()
        high = framework.predict(OutcomePredictionRequest(horizon_hours=24), 0.8, {})
        low = framework.predict(OutcomePredictionRequest(horizon_hours=24), 0.1, {})
        high_prob = next(r for r in high if r.outcome == "sepsis_onset").probability
        low_prob = next(r for r in low if r.outcome == "sepsis_onset").probability
        assert high_prob > low_prob

    def test_72h_mortality_outcome(self):
        framework = OutcomePredictionFramework()
        results = framework.predict(OutcomePredictionRequest(horizon_hours=72), 0.6, {"comorbidity_count": 4})
        outcomes = {r.outcome for r in results}
        assert "mortality_risk" in outcomes

    def test_contributing_factors_present(self):
        framework = OutcomePredictionFramework()
        results = framework.predict(
            OutcomePredictionRequest(horizon_hours=24),
            0.7,
            {"hr_mean": 110, "spo2_mean": 88},
        )
        assert any(r.contributing_factors for r in results)

    def test_sorted_by_probability(self):
        framework = OutcomePredictionFramework()
        results = framework.predict(OutcomePredictionRequest(horizon_hours=48), 0.5, {})
        probs = [r.probability for r in results]
        assert probs == sorted(probs, reverse=True)


class TestCapacityPlanning:
    def test_forecast_occupancy(self):
        cap = CapacityPlanningAnalytics()
        result = cap.forecast(current_patients=15, total_beds=20)
        assert result.current_occupancy == 75.0
        assert result.predicted_occupancy_24h > 0

    def test_surge_probability_bounded(self):
        cap = CapacityPlanningAnalytics()
        result = cap.forecast(current_patients=18, high_risk_count=8)
        assert 0 <= result.surge_probability <= 1

    def test_bed_demand_forecast(self):
        cap = CapacityPlanningAnalytics()
        result = cap.forecast(current_patients=10)
        assert len(result.bed_demand_forecast) >= 3

    def test_from_realtime_summary(self):
        cap = CapacityPlanningAnalytics()
        result = cap.from_realtime({"current_icu_patients": 12, "high_risk_count": 3})
        assert result.current_occupancy > 0


class TestResourceUtilization:
    def test_analyze_resources(self):
        res = ResourceUtilizationAnalytics()
        result = res.analyze(icu_patients=15, high_risk=5, critical_alerts=2)
        assert 0 <= result.staff_utilization <= 1
        assert len(result.forecast) == 7

    def test_bottleneck_detection(self):
        res = ResourceUtilizationAnalytics()
        result = res.analyze(icu_patients=19, high_risk=15, critical_alerts=10, total_beds=20)
        assert len(result.bottleneck_resources) >= 1

    def test_ventilator_utilization(self):
        res = ResourceUtilizationAnalytics()
        result = res.analyze(icu_patients=10, high_risk=8, critical_alerts=0)
        assert result.ventilator_utilization > 0
