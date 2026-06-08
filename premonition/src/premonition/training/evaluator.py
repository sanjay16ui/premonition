"""Model evaluator — metrics + visual outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from premonition.models.base import BaseModelWrapper
from premonition.training.metrics import ModelMetrics, compute_metrics
from premonition.training.visualizations import (
    plot_confusion_matrix,
    plot_feature_importance,
    plot_pr_curve,
    plot_roc_curve,
)
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir

logger = get_logger(__name__)


@dataclass
class EvaluationResult:
    """Metrics and plot paths for one model on one split."""

    metrics: ModelMetrics
    plot_paths: dict[str, Path] = field(default_factory=dict)


class ModelEvaluator:
    """
    Evaluate a trained model and generate visual reports.

    Simple workflow
    ---------------
    1. Model predicts probabilities on X, y.
    2. Probabilities → binary predictions (threshold = 0.5).
    3. Compute all 6 metrics + confusion matrix.
    4. Save confusion matrix, ROC, PR, and feature importance plots.
    """

    def __init__(self, reports_dir: Path, threshold: float = 0.5) -> None:
        self.reports_dir = ensure_dir(reports_dir)
        self.threshold = threshold

    def evaluate(
        self,
        model: BaseModelWrapper,
        X: np.ndarray,
        y: np.ndarray,
        split: str,
        save_plots: bool = True,
    ) -> EvaluationResult:
        """Run full evaluation for one model on one split."""
        y_prob = model.predict_proba(X)
        y_pred = (y_prob >= self.threshold).astype(int)

        metrics = compute_metrics(
            y_true=y,
            y_pred=y_pred,
            y_prob=y_prob,
            model_name=model.name,
            split=split,
            threshold=self.threshold,
        )

        plot_paths: dict[str, Path] = {}
        if save_plots:
            model_dir = self.reports_dir / model.name / split
            ensure_dir(model_dir)

            plot_paths["confusion_matrix"] = plot_confusion_matrix(
                metrics, model_dir / "confusion_matrix.png"
            )
            plot_paths["roc_curve"] = plot_roc_curve(
                y, y_prob, model_dir / "roc_curve.png", model.name, split
            )
            plot_paths["pr_curve"] = plot_pr_curve(
                y, y_prob, model_dir / "pr_curve.png", model.name, split
            )

            importance = model.get_feature_importance()
            if importance:
                plot_paths["feature_importance"] = plot_feature_importance(
                    importance,
                    model_dir / "feature_importance.png",
                    model.name,
                )

        logger.info(
            "%s [%s] — PR-AUC=%.4f  ROC-AUC=%.4f  F1=%.4f  Recall=%.4f",
            model.name,
            split,
            metrics.pr_auc,
            metrics.roc_auc,
            metrics.f1,
            metrics.recall,
        )
        return EvaluationResult(metrics=metrics, plot_paths=plot_paths)

    def print_metrics_table(self, results: list[EvaluationResult]) -> None:
        """Print a beginner-friendly comparison table to the console."""
        if not results:
            return

        split = results[0].metrics.split
        header = f"\n{'Model':<22} {'Acc':>7} {'Prec':>7} {'Rec':>7} {'F1':>7} {'ROC':>7} {'PR-AUC':>7}"
        print(f"\n=== {split.upper()} METRICS ===")
        print(header)
        print("-" * len(header))
        for r in sorted(results, key=lambda x: x.metrics.pr_auc, reverse=True):
            m = r.metrics
            print(
                f"{m.model_name:<22} {m.accuracy:>7.4f} {m.precision:>7.4f} "
                f"{m.recall:>7.4f} {m.f1:>7.4f} {m.roc_auc:>7.4f} {m.pr_auc:>7.4f}"
            )
