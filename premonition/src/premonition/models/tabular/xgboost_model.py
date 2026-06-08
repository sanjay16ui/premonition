"""XGBoost primary model for sepsis early-warning."""

from __future__ import annotations

from typing import Any

import numpy as np
import xgboost as xgb

from premonition.models.base import BaseModelWrapper


class XGBoostModel(BaseModelWrapper):
    """
    XGBoost — primary model for PREMONITION Phase 1.

    Why XGBoost as primary?
    -----------------------
    1. **Best tabular performance** — consistently wins on structured ICU data.
    2. **Handles imbalance** — `scale_pos_weight` directly addresses 15% sepsis rate.
    3. **PR-AUC optimised** — `eval_metric=aucpr` aligns with our primary metric.
    4. **Early stopping** — uses validation set to prevent overfitting.
    5. **Fast inference** — sub-millisecond predictions for real-time use later.
    6. **Feature importance** — built-in gain-based importance for clinical review.

    When might it be rejected?
    --------------------------
    If Random Forest or Logistic Regression achieves higher PR-AUC on the
    validation set, the pipeline automatically selects the winner.
    XGBoost is the *default* primary model, not a forced choice.
    """

    def build(self) -> xgb.XGBClassifier:
        return xgb.XGBClassifier(**self.params)

    def _fit_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        eval_set: list[tuple[np.ndarray, np.ndarray]] | None,
    ) -> None:
        fit_params: dict[str, Any] = {}
        if eval_set:
            fit_params["eval_set"] = eval_set
            fit_params["verbose"] = False
        self.model.fit(X, y, **fit_params)

    def _compute_importance(self) -> dict[str, float]:
        booster = self.model.get_booster()
        score = booster.get_score(importance_type="gain")
        # XGBoost uses f0, f1, ... keys — map back to real names
        mapped: dict[str, float] = {}
        for key, value in score.items():
            if key.startswith("f") and key[1:].isdigit():
                idx = int(key[1:])
                name = (
                    self.feature_names_[idx]
                    if idx < len(self.feature_names_)
                    else key
                )
                mapped[name] = float(value)
            else:
                mapped[key] = float(value)
        return mapped
