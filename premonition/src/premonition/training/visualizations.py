"""Evaluation plots — confusion matrix, feature importance, metric comparison."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # non-interactive backend (safe for servers & tests)
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import auc, precision_recall_curve, roc_curve

from premonition.training.metrics import ModelMetrics
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir

logger = get_logger(__name__)

# Consistent clinical colour palette
_COLOURS = {"negative": "#2ecc71", "positive": "#e74c3c", "accent": "#3498db"}


def plot_confusion_matrix(
    metrics: ModelMetrics,
    output_path: Path,
    title: str | None = None,
) -> Path:
    """
    Save a confusion matrix heatmap.

    Layout
    ------
              Predicted
              No    Yes
    Actual No  TN    FP
           Yes FN    TP
    """
    ensure_dir(output_path.parent)
    cm = np.array(metrics.confusion)

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["No Sepsis", "Sepsis"],
        yticklabels=["No Sepsis", "Sepsis"],
        ax=ax,
        cbar=False,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title or f"{metrics.model_name} — Confusion Matrix ({metrics.split})")

    # Add interpretation labels
    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        subtitle = f"TN={tn}  FP={fp}  FN={fn}  TP={tp}"
        ax.text(0.5, -0.15, subtitle, ha="center", transform=ax.transAxes, fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved confusion matrix -> %s", output_path)
    return output_path


def plot_feature_importance(
    importance: dict[str, float],
    output_path: Path,
    model_name: str,
    top_n: int = 20,
    title: str | None = None,
) -> Path:
    """Horizontal bar chart of top-N most important features."""
    ensure_dir(output_path.parent)

    sorted_items = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
    if not sorted_items:
        logger.warning("No feature importance to plot for %s", model_name)
        return output_path

    features, scores = zip(*sorted_items)

    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.3)))
    bars = ax.barh(range(len(features)), scores, color=_COLOURS["accent"], alpha=0.85)
    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features)
    ax.invert_yaxis()
    ax.set_xlabel("Importance Score")
    ax.set_title(title or f"{model_name} — Top {top_n} Feature Importance")

    for bar, score in zip(bars, scores):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                f" {score:.3f}", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved feature importance -> %s", output_path)
    return output_path


def plot_metrics_comparison(
    comparison: list[dict[str, Any]],
    output_path: Path,
    split: str = "val",
) -> Path:
    """Grouped bar chart comparing all models across key metrics."""
    ensure_dir(output_path.parent)

    metric_keys = ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]
    labels = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"]
    models = [row["model_name"] for row in comparison]

    x = np.arange(len(labels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(12, 6))

    for i, model in enumerate(models):
        row = next(r for r in comparison if r["model_name"] == model)
        values = [row[k] for k in metric_keys]
        offset = (i - len(models) / 2 + 0.5) * width
        ax.bar(x + offset, values, width, label=model, alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title(f"Model Comparison — {split.upper()} Split")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved metrics comparison -> %s", output_path)
    return output_path


def plot_roc_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    output_path: Path,
    model_name: str,
    split: str,
) -> Path:
    """ROC curve with AUC annotation."""
    ensure_dir(output_path.parent)
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(fpr, tpr, color=_COLOURS["accent"], lw=2, label=f"AUC = {roc_auc:.3f}")
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.5)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate (Recall)")
    ax.set_title(f"{model_name} — ROC Curve ({split})")
    ax.legend(loc="lower right")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved ROC curve -> %s", output_path)
    return output_path


def plot_pr_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    output_path: Path,
    model_name: str,
    split: str,
) -> Path:
    """Precision-Recall curve with PR-AUC annotation."""
    ensure_dir(output_path.parent)
    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    pr_auc = auc(recall, precision)
    baseline = y_true.mean()

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(recall, precision, color=_COLOURS["positive"], lw=2,
            label=f"PR-AUC = {pr_auc:.3f}")
    ax.axhline(y=baseline, color="k", linestyle="--", lw=1, alpha=0.5,
               label=f"Baseline = {baseline:.3f}")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(f"{model_name} — Precision-Recall Curve ({split})")
    ax.legend(loc="upper right")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved PR curve -> %s", output_path)
    return output_path
