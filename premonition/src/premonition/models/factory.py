"""Factory for creating model instances from configuration."""

from __future__ import annotations

from typing import Any

from premonition.models.base import BaseModelWrapper
from premonition.models.baselines.logistic import LogisticRegressionModel
from premonition.models.baselines.random_forest import RandomForestModel
from premonition.models.tabular.xgboost_model import XGBoostModel

_MODEL_MAP: dict[str, type[BaseModelWrapper]] = {
    "logistic_regression": LogisticRegressionModel,
    "random_forest": RandomForestModel,
    "xgboost": XGBoostModel,
}


def create_model(model_name: str, model_config: dict[str, Any]) -> BaseModelWrapper:
    """
    Instantiate a model wrapper by name.

    Parameters
    ----------
    model_name:
        One of: logistic_regression, random_forest, xgboost
    model_config:
        Full model_config.yaml contents (uses models.<name>.params).
    """
    if model_name not in _MODEL_MAP:
        raise ValueError(
            f"Unknown model '{model_name}'. Choose from: {list(_MODEL_MAP.keys())}"
        )

    models_cfg = model_config.get("models", {})
    if model_name not in models_cfg:
        raise KeyError(f"No configuration found for model '{model_name}'")

    params = dict(models_cfg[model_name].get("params", {}))
    cls = _MODEL_MAP[model_name]
    return cls(name=model_name, params=params)


def create_all_models(model_config: dict[str, Any]) -> list[BaseModelWrapper]:
    """Create all three Phase 1 models for comparison."""
    return [create_model(name, model_config) for name in _MODEL_MAP]
