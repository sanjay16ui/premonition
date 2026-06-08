"""Drift detection tests."""

from __future__ import annotations

import numpy as np

from premonition.mlops.drift import DriftDetector, population_stability_index


def test_psi_identical_distributions():
    data = np.random.normal(0, 1, 500)
    psi = population_stability_index(data, data)
    assert psi < 0.05


def test_psi_shifted_distributions():
    ref = np.random.normal(0, 1, 500)
    cur = np.random.normal(2, 1, 500)
    psi = population_stability_index(ref, cur)
    assert psi > 0.1


def test_feature_drift_detection():
    detector = DriftDetector(psi_threshold=0.2)
    ref = {"heart_rate": list(np.random.normal(80, 5, 200))}
    cur = {"heart_rate": list(np.random.normal(95, 5, 200))}
    drift = detector.detect_feature_drift(ref, cur)
    assert drift["heart_rate"] > 0.1


def test_prediction_drift():
    detector = DriftDetector()
    ref = list(np.random.uniform(0, 0.3, 100))
    cur = list(np.random.uniform(0.5, 0.9, 100))
    psi = detector.detect_prediction_drift(ref, cur)
    assert psi > 0.1


def test_model_drift_degradation():
    detector = DriftDetector()
    drift = detector.detect_model_drift({"pr_auc": 0.95}, {"pr_auc": 0.85})
    assert drift > 0.05


def test_full_report_flags_drift():
    detector = DriftDetector(psi_threshold=0.15)
    ref = list(np.random.normal(95, 1, 100))
    cur = list(np.random.normal(85, 1, 100))
    report = detector.full_report(
        reference_features={"spo2": ref},
        current_features={"spo2": cur},
        reference_scores=list(np.random.uniform(0, 0.2, 100)),
        current_scores=list(np.random.uniform(0.6, 0.9, 100)),
        baseline_metrics={"pr_auc": 0.95},
        current_metrics={"pr_auc": 0.80},
    )
    assert report.drifted is True
    assert report.prediction_drift > 0


def test_data_quality_check():
    detector = DriftDetector()
    issues = detector.check_data_quality({"heart_rate": float("nan"), "spo2": 98.0})
    assert any("heart_rate" in i for i in issues)
