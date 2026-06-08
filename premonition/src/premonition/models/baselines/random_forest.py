"""Random Forest baseline model."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from premonition.models.base import BaseModelWrapper


class RandomForestModel(BaseModelWrapper):
    """
    Random Forest — strong non-linear baseline.

    Why include it?
    ----------------
    - Handles mixed feature types without scaling.
    - Built-in feature importance via mean decrease in impurity.
    - Robust to outliers and missing-value patterns after imputation.
    - Common benchmark in clinical ML papers.
    """

    def build(self) -> RandomForestClassifier:
        return RandomForestClassifier(**self.params)

    def _compute_importance(self) -> dict[str, float]:
        importances = self.model.feature_importances_
        names = self.feature_names_ or [f"feature_{i}" for i in range(len(importances))]
        return dict(zip(names, importances.tolist()))
