"""End-to-end explainability pipeline — SHAP + patient reports + plots."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from premonition.config.settings import Settings, get_settings
from premonition.explainability.patient_report import PatientReportGenerator
from premonition.explainability.plots import generate_all_shap_plots
from premonition.explainability.shap_explainer import ShapExplainer
from premonition.intelligence.confidence import assess_confidence
from premonition.intelligence.predictor import PredictionIntelligence
from premonition.models.registry import ModelRegistry
from premonition.utils.logging import get_logger, setup_logging
from premonition.utils.paths import ensure_dir, timestamp_slug

logger = get_logger(__name__)


@dataclass
class ExplainabilityResult:
    """Output of a full explainability run."""

    tier: str
    model_name: str
    shap_plot_paths: dict[str, dict[str, Path]] = field(default_factory=dict)
    patient_reports: list[Path] = field(default_factory=list)
    sample_predictions: list[dict[str, Any]] = field(default_factory=list)


class ExplainabilityPipeline:
    """
    Run SHAP explainability after training.

    Steps
    -----
    1. Load best model + XGBoost (if different)
    2. Compute SHAP on validation/test data
    3. Generate global plots (summary, bar, ranking)
    4. Generate local plots (waterfall, force) for sample patients
    5. Create patient explanation reports
    """

    def __init__(
        self,
        tier: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.tier = tier or self.settings.primary_tier

    def run(
        self,
        X_processed: np.ndarray | None = None,
        patient_ids: list | None = None,
        patient_indices: list[int] | None = None,
        n_sample_patients: int = 5,
    ) -> ExplainabilityResult:
        """Execute the explainability pipeline."""
        setup_logging(self.settings.log_level)
        stamp = timestamp_slug()
        output_dir = ensure_dir(self.settings.reports_dir / self.tier / f"explainability_{stamp}")

        intel = PredictionIntelligence(tier=self.tier, settings=self.settings)
        intel.load()

        # Use test split if no data provided
        if X_processed is None:
            from premonition.data.pipeline import DataPipeline
            data = DataPipeline(tier=self.tier, settings=self.settings).run(
                save_artifacts=False
            )
            X_processed = data.X_test_processed
            if patient_ids is None and "subject_id" in data.splits.test.columns:
                patient_ids = data.splits.test["subject_id"].tolist()
            intel.set_background(data.X_train_processed)

        # Pick high-risk sample patients for local explanations
        if patient_indices is None:
            risk_scores = intel.model.predict_proba(X_processed)
            sorted_idx = np.argsort(risk_scores)[::-1]
            patient_indices = sorted_idx[:n_sample_patients].tolist()

        # Generate SHAP plots for best model + XGBoost
        shap_paths = intel.generate_shap_reports(
            X_processed,
            output_dir,
            patient_indices=patient_indices,
        )

        # Generate patient reports
        report_gen = PatientReportGenerator()
        report_paths: list[Path] = []
        sample_preds: list[dict[str, Any]] = []

        for idx in patient_indices:
            pid = patient_ids[idx] if patient_ids and idx < len(patient_ids) else idx
            risk = float(intel.model.predict_proba(X_processed[idx : idx + 1])[0])
            pred = int(risk >= intel.threshold)
            confidence = assess_confidence(risk).value

            shap_exp = intel.shap_explainer.explain(
                intel.model,
                X_processed[idx : idx + 1],
                intel.preprocessor.feature_names_out_,
                background=intel._background,
            )
            report = report_gen.generate(
                patient_id=pid,
                patient_index=0,
                risk_score=risk,
                prediction=pred,
                confidence=confidence,
                explanation=shap_exp,
                model_name=intel.model.name,
            )
            _, text_path = report_gen.save_report(report, output_dir / "patient_reports")
            report_paths.append(text_path)
            sample_preds.append(report.to_dict())

            logger.info("Patient %s: risk=%.0f%% confidence=%s", pid, risk * 100, confidence)

        return ExplainabilityResult(
            tier=self.tier,
            model_name=intel.model.name,
            shap_plot_paths=shap_paths,
            patient_reports=report_paths,
            sample_predictions=sample_preds,
        )
