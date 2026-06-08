"""Explainability service — SHAP-focused explanations via API."""

from __future__ import annotations

import asyncio

from premonition.api.schemas.requests import ExplainRequest, PatientFeaturesRequest
from premonition.api.schemas.responses import (
    ContributingFactorResponse,
    ExplainResponse,
    ShapExplanationResponse,
)
from premonition.api.schemas.validation import features_to_dataframe, prepare_tier_features
from premonition.api.services.model_loader import ModelLoaderService
from premonition.api.services.prediction import risk_category
from premonition.intelligence.confidence import assess_confidence
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


class ExplainabilityService:
    """Dedicated SHAP explanation endpoint service."""

    def __init__(self, model_loader: ModelLoaderService) -> None:
        self.model_loader = model_loader

    async def explain(
        self,
        request: ExplainRequest,
        request_id: str | None = None,
    ) -> ExplainResponse:
        if not self.model_loader.is_ready():
            raise RuntimeError("Model not loaded")

        result = await asyncio.to_thread(self._explain_sync, request)
        report = result.patient_report
        analysis = result.risk_analysis

        top_factors = [
            ContributingFactorResponse(
                rank=i + 1,
                feature=f.display_name,
                contribution_pct=round(f.contribution_pct, 1),
                direction=f.direction,
                shap_value=round(f.shap_value, 4),
                category=f.category,
            )
            for i, f in enumerate(report.top_factors[: request.top_n])
        ]

        shap_resp = ShapExplanationResponse(
            base_value=round(result.shap_explanation.base_value, 4) if result.shap_explanation else 0.0,
            top_factors=top_factors,
            risk_increasers=[r["display_name"] for r in analysis.risk_increasers],
            risk_decreasers=[r["display_name"] for r in analysis.risk_decreasers],
            dominant_category=analysis.dominant_category or None,
        )

        return ExplainResponse(
            patient_id=str(request.patient_id),
            risk_score=round(result.risk_score, 4),
            risk_pct=f"{result.risk_score * 100:.1f}%",
            confidence=result.confidence.value,
            risk_category=risk_category(result.risk_score),
            explanation_summary=report.explanation_summary,
            top_factors=top_factors,
            shap=shap_resp,
            request_id=request_id,
        )

    def _explain_sync(self, request: ExplainRequest):
        from premonition.intelligence.predictor import PredictionIntelligence

        intel = self.model_loader.state.intelligence
        registry = self.model_loader.state.feature_registry
        assert intel is not None and registry is not None

        raw_df = features_to_dataframe(request.features)
        tier_df = prepare_tier_features(raw_df, registry, self.model_loader.state.tier)
        feature_cols = [c for c in tier_df.columns if c != "subject_id"]

        return intel.predict_patient(
            tier_df[feature_cols],
            patient_id=request.patient_id,
            compute_shap=True,
        )
