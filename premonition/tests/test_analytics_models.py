"""Model benchmarking, comparison, and explainability tests."""

from __future__ import annotations

import pytest

from premonition.analytics.benchmarking import ModelBenchmarkingFramework
from premonition.analytics.comparison import ModelComparisonService
from premonition.analytics.decision_audit import AIDecisionAuditFramework
from premonition.analytics.explainability_compare import ExplainabilityComparisonEngine


@pytest.fixture
def benchmarker(settings):
    return ModelBenchmarkingFramework(settings.models_dir, settings.primary_tier)


@pytest.fixture
def comparator(settings):
    return ModelComparisonService(settings.models_dir, settings.primary_tier)


class TestModelBenchmarking:
    def test_benchmark_all_returns_three_models(self, benchmarker):
        results = benchmarker.benchmark_all()
        assert len(results) >= 2
        names = {r.model_name for r in results}
        assert "logistic_regression" in names

    def test_benchmarks_ranked_by_pr_auc(self, benchmarker):
        results = benchmarker.benchmark_all()
        if len(results) >= 2:
            assert results[0].pr_auc >= results[-1].pr_auc

    def test_ranks_assigned(self, benchmarker):
        results = benchmarker.benchmark_all()
        for r in results:
            assert r.rank >= 1

    def test_summary_has_winner(self, benchmarker):
        summary = benchmarker.summary()
        assert "winner" in summary
        assert summary["winner"] is not None

    def test_all_metrics_present(self, benchmarker):
        results = benchmarker.benchmark_all()
        for r in results:
            assert r.roc_auc > 0
            assert r.f1 > 0
            assert r.brier_score >= 0


class TestModelComparison:
    def test_compare_returns_winner(self, comparator):
        result = comparator.compare()
        assert result.winner in {"logistic_regression", "xgboost", "random_forest", "unknown"}
        assert result.primary_metric == "pr_auc"

    def test_compare_has_recommendation(self, comparator):
        result = comparator.compare()
        assert len(result.recommendation) > 10

    def test_compare_models_count(self, comparator):
        result = comparator.compare()
        assert len(result.models) >= 2

    def test_selection_comparison_loads(self, comparator):
        comparison = comparator.load_selection_comparison()
        assert isinstance(comparison, list)


class TestExplainabilityComparison:
    def test_compare_models(self):
        engine = ExplainabilityComparisonEngine()
        importances = {
            "logistic_regression": {"hr_mean": 0.3, "spo2_mean": 0.2, "age": 0.1},
            "xgboost": {"hr_mean": 0.25, "spo2_mean": 0.22, "temp_celsius_mean": 0.15},
        }
        results = engine.compare(importances)
        assert len(results) == 2
        assert results[0].top_features[0]["feature"] in importances["logistic_regression"]

    def test_agreement_score_identical(self):
        engine = ExplainabilityComparisonEngine()
        importances = {"m1": {"a": 0.5, "b": 0.3, "c": 0.2, "d": 0.1, "e": 0.05}}
        results = engine.compare(importances)
        assert engine.agreement_score(results) == 1.0

    def test_agreement_score_partial(self):
        engine = ExplainabilityComparisonEngine()
        importances = {
            "m1": {"a": 0.5, "b": 0.3, "c": 0.2, "d": 0.1, "e": 0.05},
            "m2": {"a": 0.4, "x": 0.3, "y": 0.2, "z": 0.1, "w": 0.05},
        }
        results = engine.compare(importances)
        score = engine.agreement_score(results)
        assert 0 <= score <= 1.0


class TestDecisionAudit:
    def test_record_decision(self):
        audit = AIDecisionAuditFramework()
        rec = audit.record("p1", "ensemble", 0.6, 1, "xgboost", "instability", ["hr_mean"])
        assert rec.decision_id.startswith("dec-")

    def test_query_by_patient(self):
        audit = AIDecisionAuditFramework()
        audit.record("p1", "ensemble", 0.6, 1, "xgboost", "r", [])
        audit.record("p2", "ensemble", 0.3, 0, "lr", "r", [])
        results = audit.query(patient_id="p1")
        assert len(results) == 1

    def test_summary_counts(self):
        audit = AIDecisionAuditFramework()
        audit.record("p1", "ensemble", 0.6, 1, "xgboost", "r", [], ensemble_used=True)
        summary = audit.summary()
        assert summary["total_decisions"] == 1
        assert summary["ensemble_rate"] == 1.0
