"""Tests for Section 5 explainability and prediction intelligence."""

from __future__ import annotations

import pytest

from premonition.config.settings import get_settings
from premonition.explainability.feature_labels import friendly_name
from premonition.explainability.patient_report import PatientReportGenerator
from premonition.explainability.shap_explainer import ShapExplanation, ShapExplainer
from premonition.intelligence.confidence import ConfidenceLevel, assess_confidence
from premonition.intelligence.predictor import PredictionIntelligence
from premonition.intelligence.risk_analyzer import RiskAnalyzer
from premonition.models.prediction_logger import PredictionLogger
from premonition.models.registry import ModelRegistry
from premonition.models.versioning import dataset_version


@pytest.fixture
def settings():
    return get_settings()


class TestFeatureLabels:
    def test_friendly_name(self):
        assert friendly_name("shock_index") == "Shock Index"
        assert friendly_name("hr_std") == "Heart Rate Variability"


class TestConfidence:
    def test_high_confidence(self):
        assert assess_confidence(0.95) == ConfidenceLevel.HIGH
        assert assess_confidence(0.05) == ConfidenceLevel.HIGH

    def test_low_confidence(self):
        assert assess_confidence(0.50) == ConfidenceLevel.LOW


class TestPatientReport:
    def test_report_format(self):
        exp = ShapExplanation(
            shap_values=[[0.5, 0.3, -0.1, 0.2, 0.0]],
            base_value=0.15,
            feature_names=["shock_index", "hr_std", "age", "spo2_mean", "bmi"],
            data=[[1.2, 8.0, 72, 94, 25]],
            model_name="test",
        )
        gen = PatientReportGenerator(top_n=3)
        report = gen.generate(
            patient_id=204,
            patient_index=0,
            risk_score=0.91,
            prediction=1,
            confidence="High",
            explanation=exp,
        )
        text = report.to_text()
        assert "Patient ID: 204" in text
        assert "91%" in text
        assert "High" in text
        assert len(report.top_factors) <= 3


class TestRiskAnalyzer:
    def test_increasers_and_decreasers(self):
        exp = ShapExplanation(
            shap_values=[[0.5, -0.3, 0.1]],
            base_value=0.0,
            feature_names=["shock_index", "spo2_mean", "age"],
            data=[[1.0, 95, 70]],
            model_name="test",
        )
        analysis = RiskAnalyzer().analyze(exp, 0)
        assert len(analysis.risk_increasers) >= 1
        assert len(analysis.risk_decreasers) >= 1


class TestPredictionLogger:
    def test_log_and_read(self, settings, tmp_path):
        logger = PredictionLogger(tmp_path)
        logger.log(
            patient_id=204,
            risk_score=0.91,
            prediction=1,
            confidence="High",
            model_name="logistic_regression",
            model_version="0.1.0",
            explanation_summary="High risk driven by Shock Index",
            top_factors=["Shock Index", "Heart Rate Variability"],
        )
        records = logger.read_log()
        assert len(records) == 1
        assert records[0]["patient_id"] == "204"
        assert records[0]["risk_score"] == 0.91


class TestModelRegistry:
    def test_version_file_exists(self, settings):
        version = ModelRegistry(settings.models_dir).load_version("t1")
        if version:
            assert "model_version" in version
            assert "dataset_version" in version
            assert "feature_set" in version


class TestDatasetVersion:
    def test_dataset_fingerprint(self, settings):
        info = dataset_version(settings.dataset_path)
        assert "content_hash" in info
        assert info["filename"] == "dataset.csv"


class TestPredictionIntelligence:
    def test_predict_patient(self, settings):
        from premonition.data.pipeline import DataPipeline

        data = DataPipeline(tier="t1", settings=settings).run(save_artifacts=False)
        intel = PredictionIntelligence(tier="t1", settings=settings, log_predictions=False)
        intel.load()
        intel.set_background(data.X_train_processed)

        row = data.splits.test.iloc[[0]]
        feature_cols = [c for c in row.columns if c not in {"subject_id", "sepsis_label"}]
        pid = row["subject_id"].iloc[0]

        result = intel.predict_patient(row[feature_cols], patient_id=pid)
        assert 0.0 <= result.risk_score <= 1.0
        assert result.prediction in {0, 1}
        assert result.patient_report is not None
        assert result.risk_analysis is not None
