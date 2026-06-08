"""SHAP explainability engine for PREMONITION models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import shap

from premonition.models.base import BaseModelWrapper
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ShapExplanation:
    """SHAP values for a set of predictions."""

    shap_values: np.ndarray          # (n_samples, n_features)
    base_value: float                # model baseline (expected value)
    feature_names: list[str]
    data: np.ndarray                 # processed feature matrix used
    model_name: str

    @property
    def mean_abs_shap(self) -> np.ndarray:
        """Global importance: mean |SHAP| per feature."""
        return np.abs(self.shap_values).mean(axis=0)

    def global_importance(self) -> dict[str, float]:
        """Return {feature: mean_abs_shap} sorted by importance."""
        scores = self.mean_abs_shap
        pairs = sorted(
            zip(self.feature_names, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return dict(pairs)

    def local_values(self, index: int) -> dict[str, float]:
        """SHAP values for a single patient (index into the batch)."""
        row = np.asarray(self.shap_values[index]).flatten()
        return dict(zip(self.feature_names, row.tolist()))

    def contribution_pct(self, index: int) -> dict[str, float]:
        """
        Each feature's % share of total |SHAP| for one patient.

        Used for reports like 'Shock Index (+24%)'.
        """
        row = np.abs(np.asarray(self.shap_values[index]).flatten())
        total = row.sum()
        if total == 0:
            return {f: 0.0 for f in self.feature_names}
        pcts = (row / total) * 100
        return dict(zip(self.feature_names, pcts.tolist()))


@dataclass
class ShapExplainerResult:
    """Complete SHAP analysis for one or more models."""

    explanations: dict[str, ShapExplanation] = field(default_factory=dict)
    background_samples: int = 0


class ShapExplainer:
    """
    Compute SHAP values for PREMONITION models.

    How SHAP works (simple)
    -----------------------
    SHAP answers: "How much did each feature push the prediction
    above or below the average?"

    - Positive SHAP value  -> feature INCREASED sepsis risk
    - Negative SHAP value  -> feature DECREASED sepsis risk
    - Larger absolute value -> stronger influence

    Which explainer is used?
    ------------------------
    - XGBoost / Random Forest  -> TreeExplainer (fast, exact for trees)
    - Logistic Regression      -> LinearExplainer (on scaled features)
    """

    def __init__(
        self,
        max_background_samples: int = 100,
    ) -> None:
        self.max_background_samples = max_background_samples

    def explain(
        self,
        model: BaseModelWrapper,
        X: np.ndarray,
        feature_names: list[str] | None = None,
        background: np.ndarray | None = None,
    ) -> ShapExplanation:
        """Compute SHAP values for a model on feature matrix X."""
        names = feature_names or model.feature_names_
        if not names:
            names = [f"feature_{i}" for i in range(X.shape[1])]

        bg = background if background is not None else X
        explainer_fn, transform = self._build_explainer(model, bg)
        X_use = transform(X) if transform else X

        shap_output = explainer_fn(X_use)

        # Handle different SHAP return types
        if hasattr(shap_output, "values"):
            values = shap_output.values
            base = float(np.asarray(shap_output.base_values).reshape(-1)[0])
        else:
            values = np.asarray(shap_output)
            base = 0.0

        # Binary classification may return (n, n_features, 2) — take positive class
        if values.ndim == 3:
            values = values[:, :, 1]

        logger.info(
            "SHAP computed for %s: %d samples x %d features",
            model.name, values.shape[0], values.shape[1],
        )
        return ShapExplanation(
            shap_values=values,
            base_value=base,
            feature_names=names,
            data=X_use,
            model_name=model.name,
        )

    def explain_models(
        self,
        models: list[BaseModelWrapper],
        X: np.ndarray,
        feature_names: list[str],
        background: np.ndarray | None = None,
    ) -> ShapExplainerResult:
        """Run SHAP for multiple models (e.g. best model + XGBoost)."""
        bg = background
        if bg is None:
            n = min(self.max_background_samples, len(X))
            bg = shap.sample(X, n) if len(X) > n else X

        result = ShapExplainerResult(background_samples=len(bg))
        for model in models:
            result.explanations[model.name] = self.explain(
                model, X, feature_names, background=bg
            )
        return result

    def _build_explainer(
        self,
        model: BaseModelWrapper,
        background: np.ndarray,
    ) -> tuple[Any, Any]:
        """Return (explainer_callable, optional_transform_fn)."""
        bg_sample = self._sample_background(background)

        if model.name in {"xgboost", "random_forest"}:
            tree_explainer = shap.TreeExplainer(model.model)
            return tree_explainer, None

        if model.name == "logistic_regression":
            scaler = model.model.named_steps["scaler"]
            clf = model.model.named_steps["classifier"]
            bg_scaled = scaler.transform(bg_sample)
            linear_explainer = shap.LinearExplainer(
                clf, bg_scaled, feature_perturbation="interventional"
            )

            def _explain(X: np.ndarray) -> Any:
                return linear_explainer(scaler.transform(X))

            return _explain, scaler.transform

        # Fallback: model-agnostic (slower)
        logger.warning("Using KernelExplainer fallback for %s", model.name)

        def _predict(X: np.ndarray) -> np.ndarray:
            return model.predict_proba(X)

        kernel = shap.KernelExplainer(_predict, bg_sample)

        def _explain(X: np.ndarray) -> Any:
            return kernel.shap_values(X, nsamples=100)

        return _explain, None

    def _sample_background(self, X: np.ndarray) -> np.ndarray:
        n = min(self.max_background_samples, len(X))
        if len(X) <= n:
            return X
        idx = np.random.default_rng(42).choice(len(X), size=n, replace=False)
        return X[idx]
