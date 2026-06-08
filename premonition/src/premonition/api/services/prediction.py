"""Prediction service — orchestrates ML inference for API endpoints."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from premonition.api.schemas.requests import BatchPatientItem, PatientFeaturesRequest
from premonition.api.schemas.responses import (
    BatchPredictResponse,
    ContributingFactorResponse,
    PredictResponse,
    ShapExplanationResponse,
)
from premonition.api.schemas.validation import batch_to_dataframe, features_to_dataframe, prepare_tier_features
from premonition.api.services.model_loader import ModelLoaderService
from premonition.intelligence.confidence import assess_confidence
from premonition.intelligence.predictor import PredictionResult
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


def risk_category(score: float) -> str:
    """Map risk score to clinical alert tier."""
    if score < 0.15:
        return "green"
    if score < 0.35:
        return "yellow"
    if score < 0.60:
        return "orange"
    return "red"


from cachetools import TTLCache
import json

class PredictionService:
    """Async prediction service wrapping PredictionIntelligence with caching."""

    def __init__(self, model_loader: ModelLoaderService) -> None:
        self.model_loader = model_loader
        # Cache up to 1000 predictions for 60 seconds to avoid redundant SHAP/ML inference
        self._cache = TTLCache(maxsize=1000, ttl=60)


    def _ensure_ready(self) -> None:
        if not self.model_loader.is_ready():
            raise RuntimeError(
                self.model_loader.state.load_error or "Model not loaded"
            )

    async def predict_one(
        self,
        patient_id: int | str,
        features: PatientFeaturesRequest,
        include_shap: bool = True,
        include_explanation: bool = True,
        request_id: str | None = None,
    ) -> PredictResponse:
        """Predict sepsis risk for a single patient."""
        self._ensure_ready()
        
        # Build cache key from feature vector
        features_dict = features.model_dump()
        cache_key = f"{patient_id}_{include_shap}_{include_explanation}_{hash(json.dumps(features_dict, sort_keys=True))}"
        if cache_key in self._cache:
            result = self._cache[cache_key]
        else:
            result = await asyncio.to_thread(
                self._predict_sync,
                patient_id,
                features,
                include_shap,
                request_id,
            )
            self._cache[cache_key] = result
            
        return self._to_response(result, request_id, include_explanation)

    async def predict_batch(
        self,
        patients: list[BatchPatientItem],
        include_shap: bool = False,
        include_explanation: bool = True,
        request_id: str | None = None,
    ) -> BatchPredictResponse:
        """Predict sepsis risk for multiple patients."""
        self._ensure_ready()
        results = await asyncio.to_thread(
            self._predict_batch_sync,
            patients,
            include_shap,
            request_id,
        )
        predictions = [
            self._to_response(r, request_id, include_explanation) for r in results
        ]
        return BatchPredictResponse(
            count=len(predictions),
            predictions=predictions,
            request_id=request_id,
        )

    async def predict_csv(
        self,
        df: pd.DataFrame,
        id_column: str = "subject_id",
        include_shap: bool = False,
        request_id: str | None = None,
    ) -> BatchPredictResponse:
        """Predict from uploaded CSV DataFrame."""
        self._ensure_ready()
        results = await asyncio.to_thread(
            self._predict_csv_sync,
            df,
            id_column,
            include_shap,
            request_id,
        )
        predictions = [self._to_response(r, request_id, True) for r in results]
        return BatchPredictResponse(
            count=len(predictions),
            predictions=predictions,
            request_id=request_id,
        )

    def _predict_sync(
        self,
        patient_id: int | str,
        features: PatientFeaturesRequest,
        include_shap: bool,
        request_id: str | None,
    ) -> PredictionResult:
        intel = self.model_loader.state.intelligence
        assert intel is not None
        registry = self.model_loader.state.feature_registry
        assert registry is not None

        raw_df = features_to_dataframe(features)
        tier_df = prepare_tier_features(raw_df, registry, self.model_loader.state.tier)
        feature_cols = [c for c in tier_df.columns if c not in {"subject_id"}]

        return intel.predict_patient(
            tier_df[feature_cols],
            patient_id=patient_id,
            compute_shap=include_shap,
        )

    def _predict_batch_sync(
        self,
        patients: list[BatchPatientItem],
        include_shap: bool,
        request_id: str | None,
    ) -> list[PredictionResult]:
        intel = self.model_loader.state.intelligence
        assert intel is not None
        registry = self.model_loader.state.feature_registry
        assert registry is not None

        raw_df = batch_to_dataframe(patients)
        tier_df = prepare_tier_features(raw_df, registry, self.model_loader.state.tier)

        return intel.predict_batch(
            tier_df,
            id_column="subject_id",
            compute_shap=include_shap,
        )

    def _predict_csv_sync(
        self,
        df: pd.DataFrame,
        id_column: str,
        include_shap: bool,
        request_id: str | None,
    ) -> list[PredictionResult]:
        intel = self.model_loader.state.intelligence
        assert intel is not None
        registry = self.model_loader.state.feature_registry
        assert registry is not None

        tier_df = prepare_tier_features(df, registry, self.model_loader.state.tier)
        return intel.predict_batch(tier_df, id_column=id_column, compute_shap=include_shap)

    def _to_response(
        self,
        result: PredictionResult,
        request_id: str | None,
        include_explanation: bool,
    ) -> PredictResponse:
        report = result.patient_report
        top_factors = [
            ContributingFactorResponse(
                rank=i + 1,
                feature=f.display_name,
                contribution_pct=round(f.contribution_pct, 1),
                direction=f.direction,
                shap_value=round(f.shap_value, 4),
                category=f.category,
            )
            for i, f in enumerate(report.top_factors)
        ]

        shap_resp = None
        if result.shap_explanation and result.shap_explanation.shap_values is not None:
            analysis = result.risk_analysis
            shap_resp = ShapExplanationResponse(
                base_value=round(result.shap_explanation.base_value, 4),
                top_factors=top_factors,
                risk_increasers=[r["display_name"] for r in analysis.risk_increasers],
                risk_decreasers=[r["display_name"] for r in analysis.risk_decreasers],
                dominant_category=analysis.dominant_category or None,
            )

        return PredictResponse(
            patient_id=str(result.patient_id),
            risk_score=round(result.risk_score, 4),
            risk_pct=f"{result.risk_score * 100:.1f}%",
            prediction=result.prediction,
            prediction_label="sepsis_alert" if result.prediction == 1 else "no_alert",
            confidence=result.confidence.value,
            risk_category=risk_category(result.risk_score),
            model_name=result.model_name,
            model_version=result.model_version,
            explanation_summary=report.explanation_summary if include_explanation else None,
            top_factors=top_factors if include_explanation else [],
            shap=shap_resp,
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
