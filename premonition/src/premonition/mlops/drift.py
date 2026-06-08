"""Data, prediction, and model drift detection."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class DriftReport:
    feature_drift: dict[str, float] = field(default_factory=dict)
    prediction_drift: float = 0.0
    model_drift: float = 0.0
    data_quality_issues: list[str] = field(default_factory=list)
    drifted: bool = False
    threshold: float = 0.2

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_drift": self.feature_drift,
            "prediction_drift": self.prediction_drift,
            "model_drift": self.model_drift,
            "data_quality_issues": self.data_quality_issues,
            "drifted": self.drifted,
            "threshold": self.threshold,
        }


def population_stability_index(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """PSI for numeric distributions."""
    if len(expected) == 0 or len(actual) == 0:
        return 0.0
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
    breakpoints = np.unique(breakpoints)
    if len(breakpoints) < 2:
        return 0.0
    expected_counts, _ = np.histogram(expected, bins=breakpoints)
    actual_counts, _ = np.histogram(actual, bins=breakpoints)
    expected_pct = expected_counts / max(len(expected), 1)
    actual_pct = actual_counts / max(len(actual), 1)
    psi = 0.0
    for e, a in zip(expected_pct, actual_pct):
        e = max(e, 1e-6)
        a = max(a, 1e-6)
        psi += (a - e) * math.log(a / e)
    return float(psi)


class DriftDetector:
    """Detect data drift, prediction drift, and model performance drift."""

    def __init__(self, psi_threshold: float = 0.2) -> None:
        self.psi_threshold = psi_threshold

    def check_data_quality(self, features: dict[str, float]) -> list[str]:
        issues = []
        for name, value in features.items():
            if value is None or (isinstance(value, float) and math.isnan(value)):
                issues.append(f"{name}: missing or NaN")
            elif isinstance(value, (int, float)) and value < 0 and "age" not in name.lower():
                if name in ("heart_rate", "respiratory_rate", "spo2", "temperature"):
                    pass  # valid ranges checked separately
        return issues

    def detect_feature_drift(
        self,
        reference: dict[str, list[float]],
        current: dict[str, list[float]],
    ) -> dict[str, float]:
        drift = {}
        for feature, ref_vals in reference.items():
            cur_vals = current.get(feature, [])
            if ref_vals and cur_vals:
                psi = population_stability_index(np.array(ref_vals), np.array(cur_vals))
                drift[feature] = round(psi, 4)
        return drift

    def detect_prediction_drift(
        self,
        reference_scores: list[float],
        current_scores: list[float],
    ) -> float:
        if not reference_scores or not current_scores:
            return 0.0
        return round(
            population_stability_index(np.array(reference_scores), np.array(current_scores)),
            4,
        )

    def detect_model_drift(
        self,
        baseline_metrics: dict[str, float],
        current_metrics: dict[str, float],
    ) -> float:
        """Relative degradation in primary metric (pr_auc)."""
        base = baseline_metrics.get("pr_auc", baseline_metrics.get("roc_auc", 0.0))
        cur = current_metrics.get("pr_auc", current_metrics.get("roc_auc", 0.0))
        if base <= 0:
            return 0.0
        return round(max(0.0, (base - cur) / base), 4)

    def full_report(
        self,
        reference_features: dict[str, list[float]],
        current_features: dict[str, list[float]],
        reference_scores: list[float] | None = None,
        current_scores: list[float] | None = None,
        baseline_metrics: dict[str, float] | None = None,
        current_metrics: dict[str, float] | None = None,
    ) -> DriftReport:
        feature_drift = self.detect_feature_drift(reference_features, current_features)
        pred_drift = 0.0
        if reference_scores and current_scores:
            pred_drift = self.detect_prediction_drift(reference_scores, current_scores)
        model_drift = 0.0
        if baseline_metrics and current_metrics:
            model_drift = self.detect_model_drift(baseline_metrics, current_metrics)

        max_feature = max(feature_drift.values()) if feature_drift else 0.0
        drifted = (
            max_feature > self.psi_threshold
            or pred_drift > self.psi_threshold
            or model_drift > 0.1
        )
        return DriftReport(
            feature_drift=feature_drift,
            prediction_drift=pred_drift,
            model_drift=model_drift,
            drifted=drifted,
            threshold=self.psi_threshold,
        )
