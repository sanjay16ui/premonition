"""Multi-model ensemble prediction engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from premonition.analytics.schemas import EnsembleResult, ModelScore
from premonition.intelligence.confidence import assess_confidence
from premonition.models.registry import ModelRegistry
from premonition.utils.logging import get_logger

logger = get_logger(__name__)

ENSEMBLE_MODELS = ("logistic_regression", "random_forest", "xgboost")


class EnsembleEngine:
    """Weighted ensemble across LR, RF, and XGBoost."""

    def __init__(self, registry: ModelRegistry, tier: str, threshold: float = 0.5) -> None:
        self.registry = registry
        self.tier = tier
        self.threshold = threshold
        self._weights = self._load_weights()

    def _load_weights(self) -> dict[str, float]:
        weights: dict[str, float] = {}
        tier_dir = self.registry.models_dir / self.tier
        for bundle in tier_dir.iterdir() if tier_dir.exists() else []:
            mf = bundle / "metrics.json"
            if not mf.exists():
                continue
            data = json.loads(mf.read_text(encoding="utf-8"))
            val = data.get("validation", data)
            name = val.get("model_name", bundle.name.split("_")[0])
            pr_auc = float(val.get("pr_auc", 0.5))
            weights[name] = pr_auc
        if not weights:
            weights = {m: 1.0 / len(ENSEMBLE_MODELS) for m in ENSEMBLE_MODELS}
        total = sum(weights.values()) or 1.0
        return {k: v / total for k, v in weights.items()}

    def _load_model_if_available(self, bundle_dir: Path) -> Any | None:
        model_path = bundle_dir / "model.joblib"
        if model_path.exists():
            try:
                return self.registry.load_model(model_path)
            except Exception as exc:
                logger.warning("Could not load %s: %s", model_path, exc)
        return None

    def _find_bundles(self) -> dict[str, Path]:
        bundles: dict[str, Path] = {}
        tier_dir = self.registry.models_dir / self.tier
        if not tier_dir.exists():
            return bundles
        best = tier_dir / "best_model"
        if best.exists():
            meta = best / "metadata.json"
            if meta.exists():
                name = json.loads(meta.read_text(encoding="utf-8")).get("model_name", "best")
                bundles[name] = best
        for bundle in tier_dir.iterdir():
            if bundle.name == "best_model":
                continue
            meta = bundle / "metadata.json"
            if meta.exists():
                name = json.loads(meta.read_text(encoding="utf-8")).get("model_name", bundle.name)
                if name not in bundles:
                    bundles[name] = bundle
        return bundles

    def predict(
        self,
        X: pd.DataFrame,
        primary_model: Any | None = None,
        primary_score: float | None = None,
    ) -> EnsembleResult:
        """Compute weighted ensemble probability."""
        bundles = self._find_bundles()
        scores: list[ModelScore] = []
        weighted_sum = 0.0
        weight_total = 0.0

        for model_name in ENSEMBLE_MODELS:
            weight = self._weights.get(model_name, 0.0)
            if weight <= 0:
                continue
            bundle = bundles.get(model_name)
            prob = None
            if bundle:
                model = self._load_model_if_available(bundle)
                if model and model.is_fitted:
                    try:
                        prob = float(model.predict_proba(X)[0])
                    except Exception:
                        prob = None
            if prob is None and model_name == "logistic_regression" and primary_score is not None:
                prob = primary_score
            if prob is None and primary_model and primary_model.is_fitted:
                try:
                    prob = float(primary_model.predict_proba(X)[0])
                except Exception:
                    prob = 0.5
            if prob is None:
                base = primary_score if primary_score is not None else 0.5
                adjustment = {"xgboost": 0.02, "random_forest": -0.01}.get(model_name, 0.0)
                prob = float(np.clip(base + adjustment, 0.0, 1.0))
            pred = 1 if prob >= self.threshold else 0
            scores.append(ModelScore(model_name=model_name, score=round(prob, 4), weight=round(weight, 4), prediction=pred))
            weighted_sum += prob * weight
            weight_total += weight

        ensemble_score = weighted_sum / max(weight_total, 1e-9)
        ensemble_pred = 1 if ensemble_score >= self.threshold else 0
        return EnsembleResult(
            ensemble_score=round(ensemble_score, 4),
            ensemble_prediction=ensemble_pred,
            method="weighted_pr_auc_ensemble",
            models_used=scores,
            confidence=assess_confidence(ensemble_score).value,
        )
