"""Base model wrapper — consistent interface for all PREMONITION models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BaseModelWrapper(ABC):
    """
    Thin wrapper around sklearn / XGBoost estimators.

    Every model in PREMONITION implements the same four methods so the
    training pipeline can treat them identically.
    """

    def __init__(self, name: str, params: dict[str, Any] | None = None) -> None:
        self.name = name
        self.params = params or {}
        self.model: Any = None
        self.is_fitted: bool = False
        self.feature_names_: list[str] = []

    @abstractmethod
    def build(self) -> Any:
        """Construct the underlying estimator (not yet trained)."""

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: list[str] | None = None,
        eval_set: list[tuple[np.ndarray, np.ndarray]] | None = None,
    ) -> BaseModelWrapper:
        """
        Train the model on processed feature arrays.

        Parameters
        ----------
        X:
            Training features (2-D numpy array from Section 3 preprocessor).
        y:
            Binary target array (0 = no sepsis, 1 = sepsis).
        feature_names:
            Column names after preprocessing (used for importance plots).
        eval_set:
            Optional (X_val, y_val) pairs — used by XGBoost for early stopping.
        """
        self.feature_names_ = feature_names or []
        self.model = self.build()
        self._fit_model(X, y, eval_set)
        self.is_fitted = True
        return self

    def _fit_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        eval_set: list[tuple[np.ndarray, np.ndarray]] | None,
    ) -> None:
        """Default fit — subclasses override if they need eval_set."""
        self.model.fit(X, y)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return binary predictions (0 or 1)."""
        self._check_fitted()
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return probability of the positive class (sepsis)."""
        self._check_fitted()
        proba = self.model.predict_proba(X)
        return proba[:, 1]

    def get_feature_importance(self) -> dict[str, float]:
        """
        Return {feature_name: importance_score} for plotting.

        Higher = more influential in the model's decisions.
        """
        self._check_fitted()
        return self._compute_importance()

    @abstractmethod
    def _compute_importance(self) -> dict[str, float]:
        """Model-specific importance extraction."""

    def _check_fitted(self) -> None:
        if not self.is_fitted or self.model is None:
            raise RuntimeError(f"Model '{self.name}' must be fitted before prediction.")
