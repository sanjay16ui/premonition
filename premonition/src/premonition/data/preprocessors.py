"""Sklearn-compatible preprocessing pipeline for tabular ICU features."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from premonition.features.feature_registry import FeatureRegistry
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


class OutlierCapper(BaseEstimator, TransformerMixin):
    """Clip numeric values to physiologically plausible bounds."""

    def __init__(self, caps: dict[str, list[float]] | None = None) -> None:
        self.caps = caps or {}

    def fit(self, X: pd.DataFrame, y: Any = None) -> OutlierCapper:
        self.feature_names_in_ = list(X.columns)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = X.copy()
        for col, bounds in self.caps.items():
            if col not in out.columns:
                continue
            lo, hi = bounds
            out[col] = out[col].clip(lower=lo, upper=hi)
        return out


class PremonitionPreprocessor:
    """
    End-to-end preprocessor: outlier cap → impute → one-hot encode.

    Fit only on training data. Transforms val/test without refitting.
    """

    def __init__(
        self,
        registry: FeatureRegistry,
        tier: str,
        model_config: dict[str, Any],
    ) -> None:
        self.registry = registry
        self.tier = tier.lower()
        self.model_config = model_config
        self._pipeline: Pipeline | None = None
        self.feature_names_out_: list[str] = []

        preproc_cfg = model_config.get("preprocessing", {})
        self.imputation_strategy = preproc_cfg.get("imputation_strategy", "median")
        self.outlier_caps = preproc_cfg.get("outlier_caps", {})

    @property
    def is_fitted(self) -> bool:
        return self._pipeline is not None

    def _resolve_columns(self, X: pd.DataFrame) -> tuple[list[str], list[str]]:
        """Split numeric vs categorical from the incoming tier frame."""
        categorical = [c for c in self.registry.categorical_columns if c in X.columns]
        numeric = [c for c in X.columns if c not in categorical]
        return numeric, categorical

    def _build_pipeline(self, numeric_cols: list[str], categorical_cols: list[str]) -> Pipeline:
        numeric_steps: list[tuple[str, Any]] = []
        if self.outlier_caps:
            applicable_caps = {k: v for k, v in self.outlier_caps.items() if k in numeric_cols}
            if applicable_caps:
                numeric_steps.append(("cap", OutlierCapper(caps=applicable_caps)))

        numeric_steps.append(
            ("impute", SimpleImputer(strategy=self.imputation_strategy, add_indicator=False))
        )
        numeric_pipeline = Pipeline(numeric_steps)

        transformers: list[tuple[str, Any, list[str]]] = [
            ("num", numeric_pipeline, numeric_cols),
        ]

        if categorical_cols:
            cat_pipeline = Pipeline(
                steps=[
                    ("impute", SimpleImputer(strategy="most_frequent")),
                    (
                        "onehot",
                        OneHotEncoder(
                            handle_unknown="ignore",
                            sparse_output=False,
                        ),
                    ),
                ]
            )
            transformers.append(("cat", cat_pipeline, categorical_cols))

        column_transformer = ColumnTransformer(
            transformers=transformers,
            remainder="drop",
            verbose_feature_names_out=False,
        )

        return Pipeline(steps=[("columns", column_transformer)])

    def _extract_feature_names(
        self,
        numeric_cols: list[str],
        categorical_cols: list[str],
    ) -> list[str]:
        assert self._pipeline is not None
        ct: ColumnTransformer = self._pipeline.named_steps["columns"]

        names: list[str] = list(numeric_cols)

        if categorical_cols:
            cat_transformer = ct.named_transformers_["cat"]
            ohe: OneHotEncoder = cat_transformer.named_steps["onehot"]
            cat_names = list(ohe.get_feature_names_out(categorical_cols))
            names.extend(cat_names)

        return names

    def fit(self, X: pd.DataFrame, y: Any = None) -> PremonitionPreprocessor:
        """Fit preprocessor on training features only."""
        numeric_cols, categorical_cols = self._resolve_columns(X)
        self.numeric_columns_ = numeric_cols
        self.categorical_columns_ = categorical_cols

        self._pipeline = self._build_pipeline(numeric_cols, categorical_cols)
        self._pipeline.fit(X, y)
        self.feature_names_out_ = self._extract_feature_names(numeric_cols, categorical_cols)

        logger.info(
            "Preprocessor fitted (tier=%s): %d -> %d features",
            self.tier,
            X.shape[1],
            len(self.feature_names_out_),
        )
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features to model-ready numpy array."""
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted before transform.")
        assert self._pipeline is not None
        return self._pipeline.transform(X)

    def fit_transform(self, X: pd.DataFrame, y: Any = None) -> np.ndarray:
        return self.fit(X, y).transform(X)

    def transform_to_frame(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform and return a named DataFrame (useful for SHAP)."""
        array = self.transform(X)
        return pd.DataFrame(array, columns=self.feature_names_out_, index=X.index)
