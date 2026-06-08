"""SHAP visualization plots — summary, waterfall, force, global ranking."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from premonition.explainability.feature_labels import friendly_name
from premonition.explainability.shap_explainer import ShapExplanation
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir

logger = get_logger(__name__)


def plot_shap_summary(
    explanation: ShapExplanation,
    output_path: Path,
    max_display: int = 20,
) -> Path:
    """
    SHAP Summary Plot (beeswarm).

    Shows how each feature pushes predictions across all patients.
    Red = high feature value, Blue = low feature value.
    """
    ensure_dir(output_path.parent)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(
        explanation.shap_values,
        explanation.data,
        feature_names=[friendly_name(f) for f in explanation.feature_names],
        max_display=max_display,
        show=False,
    )
    plt.title(f"SHAP Summary — {explanation.model_name}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved SHAP summary plot -> %s", output_path)
    return output_path


def plot_shap_bar(
    explanation: ShapExplanation,
    output_path: Path,
    max_display: int = 20,
) -> Path:
    """SHAP bar plot — mean |SHAP| per feature (global importance)."""
    ensure_dir(output_path.parent)
    plt.figure(figsize=(10, 8))
    shap.summary_plot(
        explanation.shap_values,
        explanation.data,
        feature_names=[friendly_name(f) for f in explanation.feature_names],
        plot_type="bar",
        max_display=max_display,
        show=False,
    )
    plt.title(f"Global Feature Importance — {explanation.model_name}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved SHAP bar plot -> %s", output_path)
    return output_path


def plot_global_feature_ranking(
    explanation: ShapExplanation,
    output_path: Path,
    top_n: int = 20,
) -> Path:
    """
    Custom horizontal bar chart of global SHAP feature ranking.

    Clearer than the default SHAP bar for CEO/clinician presentations.
    """
    ensure_dir(output_path.parent)
    importance = explanation.global_importance()
    sorted_items = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
    features = [friendly_name(f) for f, _ in sorted_items]
    scores = [s for _, s in sorted_items]

    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.35)))
    bars = ax.barh(range(len(features)), scores, color="#3498db", alpha=0.85)
    ax.set_yticks(range(len(features)))
    ax.set_yticklabels(features)
    ax.invert_yaxis()
    ax.set_xlabel("Mean |SHAP| (average impact on prediction)")
    ax.set_title(f"Global Feature Ranking — {explanation.model_name}")

    for bar, score in zip(bars, scores):
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                f" {score:.4f}", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved global feature ranking -> %s", output_path)
    return output_path


def plot_shap_waterfall(
    explanation: ShapExplanation,
    patient_index: int,
    output_path: Path,
    max_display: int = 12,
) -> Path:
    """
    SHAP Waterfall Plot for one patient.

    Shows step-by-step how each feature pushed the prediction
    from the baseline to the final risk score.
    """
    ensure_dir(output_path.parent)

    values = explanation.shap_values[patient_index]
    data_row = explanation.data[patient_index]

    explanation_obj = shap.Explanation(
        values=values,
        base_values=explanation.base_value,
        data=data_row,
        feature_names=[friendly_name(f) for f in explanation.feature_names],
    )

    plt.figure(figsize=(10, 6))
    shap.waterfall_plot(explanation_obj, max_display=max_display, show=False)
    plt.title(f"SHAP Waterfall — Patient index {patient_index}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info("Saved SHAP waterfall -> %s", output_path)
    return output_path


def plot_shap_force(
    explanation: ShapExplanation,
    patient_index: int,
    output_path: Path,
) -> Path:
    """
    SHAP Force Plot for one patient (saved as HTML).

    Visualises pushing forces: red features push risk up, blue push down.
    """
    ensure_dir(output_path.parent)

    values = explanation.shap_values[patient_index]
    data_row = explanation.data[patient_index]

    force_plot = shap.force_plot(
        explanation.base_value,
        values,
        data_row,
        feature_names=[friendly_name(f) for f in explanation.feature_names],
        matplotlib=False,
    )
    shap.save_html(str(output_path), force_plot)
    logger.info("Saved SHAP force plot -> %s", output_path)
    return output_path


def generate_all_shap_plots(
    explanation: ShapExplanation,
    output_dir: Path,
    patient_indices: list[int] | None = None,
) -> dict[str, Path]:
    """Generate the full set of SHAP plots for one model."""
    ensure_dir(output_dir)
    paths: dict[str, Path] = {}

    paths["summary"] = plot_shap_summary(
        explanation, output_dir / "shap_summary.png"
    )
    paths["bar"] = plot_shap_bar(
        explanation, output_dir / "shap_bar.png"
    )
    paths["global_ranking"] = plot_global_feature_ranking(
        explanation, output_dir / "global_feature_ranking.png"
    )

    if patient_indices:
        for idx in patient_indices:
            paths[f"waterfall_{idx}"] = plot_shap_waterfall(
                explanation, idx, output_dir / f"waterfall_patient_{idx}.png"
            )
            paths[f"force_{idx}"] = plot_shap_force(
                explanation, idx, output_dir / f"force_patient_{idx}.html"
            )

    return paths
