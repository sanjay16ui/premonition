"""Classification metrics for model comparison."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

# Map config metric names → ModelMetrics attribute names
METRIC_ALIASES: dict[str, str] = {
    "average_precision": "pr_auc",
    "pr_auc": "pr_auc",
    "roc_auc": "roc_auc",
    "f1": "f1",
    "precision": "precision",
    "recall": "recall",
    "accuracy": "accuracy",
}


def resolve_metric_name(name: str) -> str:
    """Normalise a metric name from config to a ModelMetrics attribute."""
    if name not in METRIC_ALIASES:
        raise ValueError(f"Unknown metric '{name}'. Choose from: {list(METRIC_ALIASES)}")
    return METRIC_ALIASES[name]
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class ModelMetrics:
    """Container for all evaluation metrics on one split."""

    model_name: str
    split: str  # "train" | "val" | "test"
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    pr_auc: float
    brier_score: float
    confusion: list[list[int]] = field(default_factory=list)
    n_samples: int = 0
    n_positive: int = 0
    threshold: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "split": self.split,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "roc_auc": round(self.roc_auc, 4),
            "pr_auc": round(self.pr_auc, 4),
            "brier_score": round(self.brier_score, 4),
            "confusion_matrix": self.confusion,
            "n_samples": self.n_samples,
            "n_positive": self.n_positive,
            "threshold": self.threshold,
        }


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    model_name: str,
    split: str,
    threshold: float = 0.5,
) -> ModelMetrics:
    """
    Compute the full metric suite for one model on one data split.

    Metrics explained (simple)
    --------------------------
    - **Accuracy**  : % of all predictions that were correct.
                      Misleading with imbalanced data (85% negatives).
    - **Precision** : Of patients flagged as sepsis, how many truly are?
                      High precision = fewer false alarms.
    - **Recall**    : Of all true sepsis cases, how many did we catch?
                      High recall = fewer missed deteriorations.
    - **F1**        : Balance between precision and recall.
    - **ROC-AUC**   : Overall ranking ability across all thresholds.
    - **PR-AUC**    : Precision-Recall AUC — **primary metric** for imbalanced data.
    - **Brier score**: Calibration quality (lower = better calibrated probabilities).
    """
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    y_prob = np.asarray(y_prob).astype(float)

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    return ModelMetrics(
        model_name=model_name,
        split=split,
        accuracy=float(accuracy_score(y_true, y_pred)),
        precision=float(precision_score(y_true, y_pred, zero_division=0)),
        recall=float(recall_score(y_true, y_pred, zero_division=0)),
        f1=float(f1_score(y_true, y_pred, zero_division=0)),
        roc_auc=float(roc_auc_score(y_true, y_prob)),
        pr_auc=float(average_precision_score(y_true, y_prob)),
        brier_score=float(brier_score_loss(y_true, y_prob)),
        confusion=cm.tolist(),
        n_samples=len(y_true),
        n_positive=int(y_true.sum()),
        threshold=threshold,
    )


def compare_models(
    metrics_list: list[ModelMetrics],
    primary_metric: str = "pr_auc",
) -> list[dict[str, Any]]:
    """
    Build a comparison table sorted by the primary metric (descending).

    Returns list of dicts ready for JSON export or console display.
    """
    attr = resolve_metric_name(primary_metric)
    rows = [m.to_dict() for m in metrics_list]
    rows.sort(key=lambda r: r[attr], reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows


def select_best_model(
    val_metrics: list[ModelMetrics],
    primary_metric: str = "pr_auc",
) -> str:
    """
    Pick the winning model name based on validation performance.

    Uses PR-AUC by default because our dataset is imbalanced (15% sepsis).
    """
    if not val_metrics:
        raise ValueError("No validation metrics to select from.")

    attr = resolve_metric_name(primary_metric)
    best = max(val_metrics, key=lambda m: getattr(m, attr))
    return best.model_name
