"""Logistic Regression baseline model."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from premonition.models.base import BaseModelWrapper


class LogisticRegressionModel(BaseModelWrapper):
    """
    Logistic Regression — simple, interpretable baseline.

    Why include it?
    ----------------
    - Easy to explain to clinicians (each feature has a weight).
    - Fast to train.
    - Good sanity check: if XGBoost cannot beat this, something is wrong.

    A StandardScaler is included because logistic regression is sensitive
    to feature scale (e.g. age=70 vs lactate=3.0).
    """

    def build(self) -> Pipeline:
        clf = LogisticRegression(**self.params)
        return Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("classifier", clf),
            ]
        )

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self._check_fitted()
        proba = self.model.predict_proba(X)
        return proba[:, 1]

    def _compute_importance(self) -> dict[str, float]:
        """Use absolute coefficient values as importance proxy."""
        clf: LogisticRegression = self.model.named_steps["classifier"]
        coefs = np.abs(clf.coef_[0])
        names = self.feature_names_ or [f"feature_{i}" for i in range(len(coefs))]
        return dict(zip(names, coefs.tolist()))
