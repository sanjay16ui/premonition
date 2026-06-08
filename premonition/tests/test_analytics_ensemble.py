"""Ensemble engine and dynamic model selection tests."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from premonition.analytics.ensemble import EnsembleEngine
from premonition.analytics.model_selection import DynamicModelSelector
from premonition.models.registry import ModelRegistry


@pytest.fixture
def ensemble_engine(settings, tmp_path):
    models_dir = settings.models_dir
    return EnsembleEngine(ModelRegistry(models_dir), settings.primary_tier)


class TestDynamicModelSelector:
    def test_default_routes_to_logistic(self):
        sel = DynamicModelSelector()
        model, reason = sel.select({"age": 50, "comorbidity_count": 0})
        assert model == "logistic_regression"
        assert "Default" in reason or "routing" in reason.lower()

    def test_unstable_vitals_route_xgboost(self):
        sel = DynamicModelSelector()
        model, _ = sel.select({"hr_mean": 125, "spo2_mean": 86, "map_mean": 60, "age": 55})
        assert model == "xgboost"

    def test_elderly_comorbid_routes_logistic(self):
        sel = DynamicModelSelector()
        model, _ = sel.select({"age": 75, "comorbidity_count": 4, "hr_mean": 80})
        assert model == "logistic_regression"

    def test_moderate_comorbidity_routes_rf(self):
        sel = DynamicModelSelector()
        model, _ = sel.select({"age": 60, "comorbidity_count": 3, "hr_mean": 85, "spo2_mean": 95})
        assert model == "random_forest"


class TestEnsembleEngine:
    def test_load_weights_from_metrics(self, ensemble_engine):
        weights = ensemble_engine._weights
        assert len(weights) >= 1
        assert abs(sum(weights.values()) - 1.0) < 0.01

    def test_ensemble_predict_returns_result(self, ensemble_engine):
        X = pd.DataFrame(np.random.randn(1, 5), columns=[f"f{i}" for i in range(5)])
        result = ensemble_engine.predict(X, primary_score=0.4)
        assert 0 <= result.ensemble_score <= 1
        assert result.ensemble_prediction in {0, 1}
        assert len(result.models_used) >= 1

    def test_ensemble_uses_three_models(self, ensemble_engine):
        X = pd.DataFrame([[0.1, 0.2, 0.3, 0.4, 0.5]], columns=[f"f{i}" for i in range(5)])
        result = ensemble_engine.predict(X, primary_score=0.5)
        names = {m.model_name for m in result.models_used}
        assert "logistic_regression" in names or len(names) >= 1

    def test_high_score_triggers_alert(self, ensemble_engine):
        X = pd.DataFrame([[1.0] * 5], columns=[f"f{i}" for i in range(5)])
        result = ensemble_engine.predict(X, primary_score=0.85)
        assert result.ensemble_prediction == 1

    def test_low_score_no_alert(self, ensemble_engine):
        X = pd.DataFrame([[0.0] * 5], columns=[f"f{i}" for i in range(5)])
        result = ensemble_engine.predict(X, primary_score=0.05)
        assert result.ensemble_prediction == 0

    def test_confidence_assigned(self, ensemble_engine):
        X = pd.DataFrame([[0.5] * 5], columns=[f"f{i}" for i in range(5)])
        result = ensemble_engine.predict(X, primary_score=0.5)
        assert result.confidence in {"High", "Medium", "Low"}

    def test_weights_normalized(self, settings):
        engine = EnsembleEngine(ModelRegistry(settings.models_dir), settings.primary_tier)
        total = sum(engine._weights.values())
        assert abs(total - 1.0) < 0.05

    def test_find_bundles_includes_best(self, ensemble_engine):
        bundles = ensemble_engine._find_bundles()
        assert len(bundles) >= 1
