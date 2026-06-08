"""Prediction Intelligence Layer — predict + explain in one call."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from premonition.config.settings import Settings, get_settings
from premonition.data.preprocessors import PremonitionPreprocessor
from premonition.explainability.patient_report import PatientExplanationReport, PatientReportGenerator
from premonition.explainability.plots import generate_all_shap_plots
from premonition.explainability.shap_explainer import ShapExplainer, ShapExplanation
from premonition.intelligence.confidence import ConfidenceLevel, assess_confidence
from premonition.intelligence.risk_analyzer import RiskAnalysis, RiskAnalyzer
from premonition.models.base import BaseModelWrapper
from premonition.models.prediction_logger import PredictionLogger
from premonition.models.registry import ModelRegistry
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir

logger = get_logger(__name__)


@dataclass
class PredictionResult:
    """Complete prediction with explanation for one patient."""

    patient_id: int | str
    risk_score: float
    prediction: int
    confidence: ConfidenceLevel
    model_name: str
    model_version: str
    patient_report: PatientExplanationReport
    risk_analysis: RiskAnalysis
    shap_explanation: ShapExplanation | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "risk_score": round(self.risk_score, 4),
            "risk_pct": f"{self.risk_score * 100:.0f}%",
            "prediction": self.prediction,
            "confidence": self.confidence.value,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "patient_report": self.patient_report.to_dict(),
            "risk_analysis": self.risk_analysis.to_dict(),
        }


class PredictionIntelligence:
    """
    The brain of PREMONITION predictions.

    Does NOT just return a risk score. It also answers:
    - WHY is this patient at risk?
    - WHAT features pushed risk up or down?
    - HOW confident is the model?

    Usage
    -----
    >>> intel = PredictionIntelligence(tier="t1")
    >>> intel.load()
    >>> result = intel.predict_patient(patient_row, patient_id=204)
    >>> print(result.patient_report.to_text())
    """

    def __init__(
        self,
        tier: str | None = None,
        settings: Settings | None = None,
        threshold: float = 0.5,
        log_predictions: bool = True,
    ) -> None:
        self.settings = settings or get_settings()
        self.tier = tier or self.settings.primary_tier
        self.threshold = threshold
        self.log_predictions = log_predictions

        self.registry = ModelRegistry(self.settings.models_dir)
        self.shap_explainer = ShapExplainer(
            max_background_samples=self.settings.model_config.get("shap", {}).get(
                "max_samples", 100
            )
        )
        self.report_generator = PatientReportGenerator(top_n=5)
        self.risk_analyzer = RiskAnalyzer()
        self.prediction_logger = PredictionLogger(self.settings.logs_dir)

        self.model: BaseModelWrapper | None = None
        self.comparison_model: BaseModelWrapper | None = None
        self.preprocessor: PremonitionPreprocessor | None = None
        self.model_version: str = "unknown"
        self._background: np.ndarray | None = None

    def load(self) -> None:
        """Load best model, preprocessor, and optionally XGBoost for SHAP comparison."""
        self.model = self.registry.load_best_model(self.tier)
        self.preprocessor = self.registry.load_preprocessor(self.tier)
        metadata = self.registry.load_metadata(self.tier)
        self.model_version = metadata.get("model_version", "0.1.0")
        logger.info(
            "Loaded model '%s' v%s (tier=%s)",
            self.model.name, self.model_version, self.tier,
        )

        # Also load XGBoost for SHAP if it is not the best model
        if self.model.name != "xgboost":
            try:
                self.comparison_model = self._load_xgboost_model()
            except FileNotFoundError:
                logger.info("No separate XGBoost artifact found for SHAP comparison")

    def _load_xgboost_model(self) -> BaseModelWrapper:
        tier_dir = self.settings.models_dir / self.tier
        xgb_dirs = sorted(tier_dir.glob("xgboost_*"), reverse=True)
        if not xgb_dirs:
            raise FileNotFoundError("No XGBoost model artifacts found")
        return self.registry.load_model(xgb_dirs[0] / "model.joblib")

    def set_background(self, X_processed: np.ndarray) -> None:
        """Set background data for SHAP (typically training set sample)."""
        self._background = X_processed

    def predict_patient(
        self,
        patient_features: pd.DataFrame,
        patient_id: int | str,
        compute_shap: bool = True,
    ) -> PredictionResult:
        """
        Predict and fully explain one patient.

        Parameters
        ----------
        patient_features:
            Single-row DataFrame with raw tier features (pre-preprocessing).
        patient_id:
            Patient identifier for the report.
        compute_shap:
            Whether to compute SHAP values (slightly slower).
        """
        if self.model is None or self.preprocessor is None:
            raise RuntimeError("Call load() before predict_patient()")

        X_processed = self.preprocessor.transform(patient_features)
        risk_score = float(self.model.predict_proba(X_processed)[0])
        prediction = int(risk_score >= self.threshold)
        confidence = assess_confidence(risk_score)

        shap_exp = None
        if compute_shap:
            shap_exp = self.shap_explainer.explain(
                self.model,
                X_processed,
                self.preprocessor.feature_names_out_,
                background=self._background,
            )

        report = self.report_generator.generate(
            patient_id=patient_id,
            patient_index=0,
            risk_score=risk_score,
            prediction=prediction,
            confidence=confidence.value,
            explanation=shap_exp or _empty_shap(self.model),
            model_name=self.model.name,
        )

        analysis = (
            self.risk_analyzer.analyze(shap_exp, 0)
            if shap_exp
            else RiskAnalysis()
        )

        result = PredictionResult(
            patient_id=patient_id,
            risk_score=risk_score,
            prediction=prediction,
            confidence=confidence,
            model_name=self.model.name,
            model_version=self.model_version,
            patient_report=report,
            risk_analysis=analysis,
            shap_explanation=shap_exp,
        )

        if self.log_predictions:
            self.prediction_logger.log(
                patient_id=patient_id,
                risk_score=risk_score,
                prediction=prediction,
                confidence=confidence.value,
                model_name=self.model.name,
                model_version=self.model_version,
                explanation_summary=report.explanation_summary,
                top_factors=[f.display_name for f in report.top_factors],
            )

        return result

    def predict_batch(
        self,
        patients_df: pd.DataFrame,
        id_column: str = "subject_id",
        compute_shap: bool = True,
    ) -> list[PredictionResult]:
        """Predict and explain a batch of patients."""
        if self.model is None or self.preprocessor is None:
            raise RuntimeError("Call load() before predict_batch()")

        feature_cols = [
            c for c in patients_df.columns if c not in {id_column, "sepsis_label"}
        ]
        X_raw = patients_df[feature_cols]
        X_processed = self.preprocessor.transform(X_raw)
        risk_scores = self.model.predict_proba(X_processed)
        predictions = (risk_scores >= self.threshold).astype(int)

        shap_exp = None
        if compute_shap:
            shap_exp = self.shap_explainer.explain(
                self.model,
                X_processed,
                self.preprocessor.feature_names_out_,
                background=self._background,
            )

        results: list[PredictionResult] = []
        for i in range(len(patients_df)):
            pid = patients_df.iloc[i][id_column] if id_column in patients_df.columns else i
            confidence = assess_confidence(float(risk_scores[i]))

            report = self.report_generator.generate(
                patient_id=pid,
                patient_index=i if shap_exp is not None else 0,
                risk_score=float(risk_scores[i]),
                prediction=int(predictions[i]),
                confidence=confidence.value,
                explanation=shap_exp or _empty_shap(self.model),
                model_name=self.model.name,
            )
            analysis = (
                self.risk_analyzer.analyze(shap_exp, i) if shap_exp else RiskAnalysis()
            )

            result = PredictionResult(
                patient_id=pid,
                risk_score=float(risk_scores[i]),
                prediction=int(predictions[i]),
                confidence=confidence,
                model_name=self.model.name,
                model_version=self.model_version,
                patient_report=report,
                risk_analysis=analysis,
                shap_explanation=shap_exp,
            )

            if self.log_predictions:
                self.prediction_logger.log(
                    patient_id=pid,
                    risk_score=result.risk_score,
                    prediction=result.prediction,
                    confidence=confidence.value,
                    model_name=self.model.name,
                    model_version=self.model_version,
                    explanation_summary=report.explanation_summary,
                    top_factors=[f.display_name for f in report.top_factors],
                )
            results.append(result)

        return results

    def generate_shap_reports(
        self,
        X_processed: np.ndarray,
        output_dir: Path,
        patient_indices: list[int] | None = None,
        models: list[BaseModelWrapper] | None = None,
    ) -> dict[str, dict[str, Path]]:
        """
        Generate full SHAP visualisation suite for best model + XGBoost.

        Returns {model_name: {plot_name: path}}.
        """
        ensure_dir(output_dir)
        target_models = models or [self.model]
        if self.comparison_model and self.comparison_model not in target_models:
            target_models.append(self.comparison_model)

        all_paths: dict[str, dict[str, Path]] = {}
        for model in target_models:
            if model is None:
                continue
            exp = self.shap_explainer.explain(
                model,
                X_processed,
                self.preprocessor.feature_names_out_ if self.preprocessor else [],
                background=self._background,
            )
            model_dir = output_dir / model.name
            all_paths[model.name] = generate_all_shap_plots(
                exp, model_dir, patient_indices=patient_indices
            )
        return all_paths


def _empty_shap(model: BaseModelWrapper) -> ShapExplanation:
    """Stub when SHAP is skipped."""
    from premonition.explainability.shap_explainer import ShapExplanation
    return ShapExplanation(
        shap_values=np.zeros((1, len(model.feature_names_) or 1)),
        base_value=0.0,
        feature_names=model.feature_names_ or ["feature_0"],
        data=np.zeros((1, len(model.feature_names_) or 1)),
        model_name=model.name,
    )
