"""Tests for Section 4 training pipeline."""

from __future__ import annotations

import pytest

from premonition.config.settings import get_settings
from premonition.models.factory import create_all_models
from premonition.training.metrics import compute_metrics, select_best_model
from premonition.training.pipeline import TrainingPipeline
from premonition.training.trainer import ModelTrainer


@pytest.fixture
def settings():
    return get_settings()


class TestModelFactory:
    def test_creates_three_models(self, settings):
        models = create_all_models(settings.model_config)
        names = {m.name for m in models}
        assert names == {"logistic_regression", "random_forest", "xgboost"}


class TestMetrics:
    def test_compute_metrics_perfect_prediction(self):
        y = [0, 0, 1, 1]
        metrics = compute_metrics(y, y, [0.0, 0.0, 1.0, 1.0], "test", "val")
        assert metrics.accuracy == 1.0
        assert metrics.pr_auc == 1.0

    def test_select_best_by_pr_auc(self):
        from premonition.training.metrics import ModelMetrics

        m1 = ModelMetrics("a", "val", 0.9, 0.5, 0.5, 0.5, 0.8, 0.6, 0.1)
        m2 = ModelMetrics("b", "val", 0.85, 0.6, 0.7, 0.65, 0.85, 0.75, 0.1)
        best = select_best_model([m1, m2], primary_metric="pr_auc")
        assert best == "b"


class TestTrainingPipeline:
    def test_full_pipeline_runs(self, settings):
        pipeline = TrainingPipeline(tier="t1", settings=settings)
        result = pipeline.run(save_artifacts=False)

        assert len(result.trained_models) == 3
        assert result.best_model_name in {
            "logistic_regression", "random_forest", "xgboost"
        }
        assert result.test_result is not None
        assert result.test_result.metrics.pr_auc > 0
        assert len(result.comparison) == 3

    def test_all_models_fitted(self, settings):
        pipeline = TrainingPipeline(tier="t1", settings=settings)
        result = pipeline.run(save_artifacts=False)
        for tm in result.trained_models:
            assert tm.model.is_fitted

    def test_test_only_for_best(self, settings):
        """Validation has 3 results; test has 1 (best model only)."""
        pipeline = TrainingPipeline(tier="t1", settings=settings)
        result = pipeline.run(save_artifacts=False)
        assert len(result.val_results) == 3
        assert result.test_result.metrics.model_name == result.best_model_name
