"""MLOps promotion, evaluation, and monitoring tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from premonition.mlops.evaluation import compare_models, save_evaluation_report
from premonition.mlops.monitoring import FeatureMonitor, PredictionMonitor
from premonition.mlops.promotion import ModelPromotionService


@pytest.fixture
def promotion_svc(tmp_path):
    models_dir = tmp_path / "models"
    best = models_dir / "t1" / "best_model"
    best.mkdir(parents=True)
    (best / "version.json").write_text(json.dumps({"model_version": "v1.0.0"}))
    (best / "metrics.json").write_text(json.dumps({"pr_auc": 0.95, "roc_auc": 0.97}))
    (best / "model.joblib").write_text("stub")
    return ModelPromotionService(models_dir)


def test_promote_to_staging(promotion_svc):
    result = promotion_svc.promote_to_staging("t1", "admin@test")
    assert result["stage"] == "staging"
    assert (promotion_svc.staging_dir / "t1" / "version.json").exists()


def test_approve_for_production(promotion_svc):
    promotion_svc.promote_to_staging("t1", "admin@test")
    result = promotion_svc.approve_for_production("t1", "admin@test")
    assert result["stage"] == "production"


def test_rollback_production(promotion_svc):
    promotion_svc.promote_to_staging("t1", "admin@test")
    promotion_svc.approve_for_production("t1", "admin@test")
    promotion_svc.promote_to_staging("t1", "admin@test")
    promotion_svc.approve_for_production("t1", "admin@test")
    result = promotion_svc.rollback_production("t1", "admin@test")
    assert result["action"] == "rollback"


def test_promotion_history(promotion_svc):
    promotion_svc.promote_to_staging("t1", "admin@test")
    history = promotion_svc.get_promotion_history()
    assert len(history) >= 1
    assert history[0]["action"] == "promote_staging"


def test_model_comparison():
    report = compare_models({"pr_auc": 0.90}, {"pr_auc": 0.95})
    assert report["recommended"] == "model_b"


def test_feature_monitor():
    mon = FeatureMonitor()
    mon.record({"heart_rate": 80.0, "spo2": 97.0})
    summary = mon.summary()
    assert "heart_rate" in summary
    assert summary["heart_rate"]["mean"] == 80.0


def test_prediction_monitor():
    mon = PredictionMonitor()
    mon.record(0.8, is_alert=True)
    mon.record(0.2, is_alert=False)
    summary = mon.summary()
    assert summary["total_predictions"] == 2
    assert summary["alert_count"] == 1


def test_save_evaluation_report(tmp_path):
    path = save_evaluation_report(tmp_path / "report.json", {"score": 0.95})
    assert path.exists()
