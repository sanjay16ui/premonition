"""Clinical rules, recommendations, escalation, alert prioritization tests."""

from __future__ import annotations

import pytest

from premonition.analytics.alert_prioritization import AlertPrioritizationAI
from premonition.analytics.clinical_rules import ClinicalRuleEngine
from premonition.analytics.escalation import SmartEscalationWorkflow
from premonition.analytics.recommendations import ClinicalRecommendationRanker
from premonition.analytics.schemas import RecommendationRequest
from premonition.analytics.trajectory import PatientTrajectoryAnalyzer


class TestClinicalRules:
    def test_normal_vitals_no_critical(self):
        engine = ClinicalRuleEngine()
        rules = engine.evaluate({"temp_celsius_mean": 37, "hr_mean": 75, "spo2_mean": 97, "map_mean": 85}, 0.1)
        critical = [r for r in rules if r.severity == "critical" and r.triggered]
        assert len(critical) == 0

    def test_hypoxemia_triggers(self):
        engine = ClinicalRuleEngine()
        rules = engine.evaluate({"spo2_mean": 88}, 0.2)
        names = [r.name for r in rules if r.triggered]
        assert "hypoxemia" in names

    def test_high_ml_risk_triggers(self):
        engine = ClinicalRuleEngine()
        rules = engine.evaluate({}, 0.6)
        names = [r.name for r in rules if r.triggered]
        assert "ml_high_risk" in names

    def test_hypotension_critical(self):
        engine = ClinicalRuleEngine()
        rules = engine.evaluate({"map_mean": 55}, 0.2)
        critical = [r for r in rules if r.name == "hypotension" and r.triggered]
        assert len(critical) == 1

    def test_clinical_score_bounded(self):
        engine = ClinicalRuleEngine()
        score = engine.clinical_score({"spo2_mean": 85, "hr_mean": 110, "map_mean": 60}, 0.7)
        assert 0 <= score <= 1.0


class TestRecommendations:
    def test_rank_returns_actions(self):
        ranker = ClinicalRecommendationRanker()
        recs = ranker.rank(RecommendationRequest(risk_score=0.6))
        assert len(recs) >= 3
        assert recs[0].rank == 1

    def test_critical_risk_prioritizes_abx(self):
        ranker = ClinicalRecommendationRanker()
        recs = ranker.rank(RecommendationRequest(risk_score=0.7))
        actions = [r.action.lower() for r in recs]
        assert any("antibiotic" in a for a in actions)

    def test_low_risk_fewer_critical(self):
        ranker = ClinicalRecommendationRanker()
        recs = ranker.rank(RecommendationRequest(risk_score=0.1))
        critical = [r for r in recs if r.priority == "critical"]
        assert len(critical) <= 2


class TestEscalation:
    def test_low_risk_minimal_escalation(self):
        wf = SmartEscalationWorkflow()
        result = wf.evaluate(0.1, 0.0, "GREEN")
        assert result["escalation_level"] <= 2

    def test_black_alert_max_escalation(self):
        wf = SmartEscalationWorkflow()
        result = wf.evaluate(0.8, 0.1, "BLACK")
        assert result["escalation_level"] == 5

    def test_velocity_increases_level(self):
        wf = SmartEscalationWorkflow()
        base = wf.evaluate(0.2, 0.0, "GREEN")
        fast = wf.evaluate(0.2, 0.25, "GREEN")
        assert fast["escalation_level"] >= base["escalation_level"]


class TestAlertPrioritization:
    def test_prioritize_by_level(self):
        ai = AlertPrioritizationAI()
        alerts = [
            {"level": "GREEN", "risk_score": 0.1},
            {"level": "RED", "risk_score": 0.7},
            {"level": "BLACK", "risk_score": 0.9},
        ]
        ranked = ai.prioritize(alerts)
        assert ranked[0]["level"] == "BLACK"

    def test_top_critical_limit(self):
        ai = AlertPrioritizationAI()
        alerts = [{"level": "RED", "risk_score": 0.5 + i * 0.05} for i in range(10)]
        top = ai.top_critical(alerts, n=3)
        assert len(top) == 3


class TestTrajectory:
    def test_empty_history(self):
        analyzer = PatientTrajectoryAnalyzer()
        result = analyzer.analyze_history([])
        assert result["trend"] == "stable"

    def test_deteriorating_trend(self):
        analyzer = PatientTrajectoryAnalyzer()
        history = [
            {"timestamp": "t1", "risk_score": 0.2},
            {"timestamp": "t2", "risk_score": 0.5},
            {"timestamp": "t3", "risk_score": 0.7},
        ]
        result = analyzer.analyze_history(history)
        assert result["trend"] in {"deteriorating", "rapidly_deteriorating"}

    def test_forecast_trajectory(self):
        analyzer = PatientTrajectoryAnalyzer()
        forecast = analyzer.predict_trajectory(0.5, 0.1, hours=6)
        assert len(forecast) == 6
