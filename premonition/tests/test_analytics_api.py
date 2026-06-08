"""Analytics API endpoint integration tests."""

from __future__ import annotations

import pytest

from premonition.api.version import API_PREFIX

ANALYTICS = f"{API_PREFIX}/analytics"


class TestAnalyticsExecutive:
    def test_executive_endpoint(self, client):
        resp = client.get(f"{ANALYTICS}/executive")
        assert resp.status_code == 200
        data = resp.json()
        assert "kpis" in data
        assert "model_performance" in data

    def test_executive_has_operational_status(self, client):
        resp = client.get(f"{ANALYTICS}/executive")
        assert "operational_status" in resp.json()


class TestAnalyticsPopulation:
    def test_population_endpoint(self, client):
        resp = client.get(f"{ANALYTICS}/population")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_patients"] > 0
        assert "sepsis_incidence" in data

    def test_population_demographics(self, client):
        resp = client.get(f"{ANALYTICS}/population")
        assert "demographic_breakdown" in resp.json()


class TestAnalyticsCohorts:
    def test_cohorts_get(self, client):
        resp = client.get(f"{ANALYTICS}/cohorts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_cohort_analysis_post(self, client):
        resp = client.post(f"{ANALYTICS}/cohort-analysis", json={"segment_by": "gender"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAnalyticsOutcomes:
    def test_outcomes_get(self, client):
        resp = client.get(f"{ANALYTICS}/outcomes")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_outcome_prediction_post(self, client):
        resp = client.post(f"{ANALYTICS}/outcome-prediction", json={
            "horizon_hours": 48,
            "patient_features": {"hr_mean": 105, "spo2_mean": 93, "comorbidity_count": 2},
        })
        assert resp.status_code == 200
        outcomes = resp.json()
        assert len(outcomes) >= 1


class TestAnalyticsCapacity:
    def test_capacity_endpoint(self, client):
        resp = client.get(f"{ANALYTICS}/capacity")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_occupancy" in data
        assert "surge_probability" in data


class TestAnalyticsResources:
    def test_resources_endpoint(self, client):
        resp = client.get(f"{ANALYTICS}/resources")
        assert resp.status_code == 200
        data = resp.json()
        assert "staff_utilization" in data


class TestAnalyticsKPIs:
    def test_kpis_endpoint(self, client):
        resp = client.get(f"{ANALYTICS}/kpis")
        assert resp.status_code == 200
        data = resp.json()
        assert "sepsis_detection_rate" in data
        assert "model_uptime_pct" in data


class TestAnalyticsSimulate:
    def test_simulate_icu_surge(self, client):
        resp = client.post(f"{ANALYTICS}/simulate", json={
            "scenario": "icu_surge",
            "parameters": {"patients": 18, "beds": 20, "high_risk": 6},
        })
        assert resp.status_code == 200

    def test_simulate_sepsis_outbreak(self, client):
        resp = client.post(f"{ANALYTICS}/simulate", json={
            "scenario": "sepsis_outbreak",
            "parameters": {"multiplier": 1.5, "patients": 30},
        })
        assert resp.status_code == 200
        assert "projected_rate" in resp.json()


class TestAnalyticsCompareModels:
    def test_compare_models(self, client):
        resp = client.post(f"{ANALYTICS}/compare-models")
        assert resp.status_code == 200
        data = resp.json()
        assert "winner" in data
        assert len(data["models"]) >= 2


class TestAnalyticsRecommendations:
    def test_recommendations_high_risk(self, client):
        resp = client.post(f"{ANALYTICS}/recommendations", json={"risk_score": 0.7})
        assert resp.status_code == 200
        recs = resp.json()
        assert len(recs) >= 3
        assert recs[0]["rank"] == 1


class TestAnalyticsRiskStratification:
    def test_risk_stratification(self, client):
        resp = client.post(f"{ANALYTICS}/risk-stratification", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "tiers" in data
        assert data["total_patients"] > 0
