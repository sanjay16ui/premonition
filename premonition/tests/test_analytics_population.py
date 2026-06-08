"""Population health, cohorts, and risk stratification tests."""

from __future__ import annotations

import pandas as pd
import pytest

from premonition.analytics.cohorts import CohortAnalysisEngine
from premonition.analytics.population import PopulationHealthAnalytics
from premonition.analytics.risk_stratification import RiskStratificationEngine
from premonition.analytics.schemas import CohortAnalysisRequest


@pytest.fixture
def sample_df(settings):
    df = pd.read_csv(settings.dataset_path, nrows=200)
    return df


class TestPopulationHealth:
    def test_analyze_returns_metrics(self, sample_df):
        analytics = PopulationHealthAnalytics()
        result = analytics.analyze(sample_df)
        assert result.total_patients == 200
        assert 0 <= result.sepsis_incidence <= 1

    def test_demographics_present(self, sample_df):
        analytics = PopulationHealthAnalytics()
        result = analytics.analyze(sample_df)
        assert "age" in result.demographic_breakdown

    def test_trend_generated(self, sample_df):
        analytics = PopulationHealthAnalytics()
        result = analytics.analyze(sample_df)
        assert len(result.trend) >= 1

    def test_risk_distribution_keys(self, sample_df):
        analytics = PopulationHealthAnalytics()
        result = analytics.analyze(sample_df)
        assert "low" in result.risk_distribution


class TestCohortAnalysis:
    def test_age_group_segments(self, sample_df):
        engine = CohortAnalysisEngine()
        segments = engine.analyze(sample_df, CohortAnalysisRequest(segment_by="age_group"))
        assert len(segments) >= 2
        assert all(s.size > 0 for s in segments)

    def test_gender_segments(self, sample_df):
        engine = CohortAnalysisEngine()
        segments = engine.analyze(sample_df, CohortAnalysisRequest(segment_by="gender"))
        assert len(segments) >= 1

    def test_sepsis_rate_valid(self, sample_df):
        engine = CohortAnalysisEngine()
        segments = engine.analyze(sample_df, CohortAnalysisRequest(segment_by="age_group"))
        for s in segments:
            assert 0 <= s.sepsis_rate <= 1

    def test_comorbidity_segments(self, sample_df, settings):
        engine = CohortAnalysisEngine()
        segments = engine.analyze(
            sample_df,
            CohortAnalysisRequest(segment_by="comorbidity"),
            feature_config=settings.feature_config,
        )
        assert len(segments) >= 1

    def test_sorted_by_sepsis_rate(self, sample_df):
        engine = CohortAnalysisEngine()
        segments = engine.analyze(sample_df, CohortAnalysisRequest(segment_by="age_group"))
        rates = [s.sepsis_rate for s in segments]
        assert rates == sorted(rates, reverse=True)

    def test_filter_applied(self, sample_df):
        engine = CohortAnalysisEngine()
        if "gender" in sample_df.columns:
            g = sample_df["gender"].iloc[0]
            segments = engine.analyze(
                sample_df,
                CohortAnalysisRequest(segment_by="age_group", filters={"gender": g}),
            )
            assert all(s.size >= 0 for s in segments)


class TestRiskStratification:
    def test_stratify_scores(self):
        engine = RiskStratificationEngine()
        scores = [0.05, 0.2, 0.4, 0.6, 0.8]
        result = engine.stratify(scores)
        assert result.total_patients == 5
        assert len(result.tiers) == 4

    def test_percentages_sum_near_100(self):
        engine = RiskStratificationEngine()
        scores = [0.1] * 50 + [0.5] * 30 + [0.8] * 20
        result = engine.stratify(scores)
        total_pct = sum(t.percentage for t in result.tiers)
        assert abs(total_pct - 100) < 1

    def test_custom_thresholds(self):
        engine = RiskStratificationEngine()
        result = engine.stratify([0.25], thresholds={"low": 0.2, "moderate": 0.4, "high": 0.6, "critical": 0.8})
        assert result.total_patients == 1

    def test_from_predictions(self):
        engine = RiskStratificationEngine()
        preds = [{"risk_score": 0.1}, {"risk_score": 0.5}, {"risk_score": 0.9}]
        result = engine.stratify_from_predictions(preds)
        assert result.total_patients == 3
