"""Model trainer — fit models on the training split."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from premonition.data.pipeline import DataPipelineResult
from premonition.models.base import BaseModelWrapper
from premonition.models.factory import create_all_models
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TrainedModel:
    """A fitted model ready for evaluation."""

    model: BaseModelWrapper
    feature_names: list[str] = field(default_factory=list)


class ModelTrainer:
    """
    Train all candidate models on the processed training split.

    Simple workflow
    ---------------
    1. Receive processed arrays from Section 3 DataPipeline.
    2. Create 3 model instances (Logistic Regression, Random Forest, XGBoost).
    3. Fit each on X_train_processed / y_train.
    4. XGBoost additionally receives the validation set for early stopping.
    """

    def __init__(self, model_config: dict) -> None:
        self.model_config = model_config

    def train_all(self, data: DataPipelineResult) -> list[TrainedModel]:
        """Train every candidate model and return fitted wrappers."""
        models = create_all_models(self.model_config)
        trained: list[TrainedModel] = []

        X_train = data.X_train_processed
        y_train = data.y_train.values
        X_val = data.X_val_processed
        y_val = data.y_val.values
        feature_names = data.processed_feature_names

        for model in models:
            logger.info("Training %s on %d samples …", model.name, len(y_train))

            eval_set = None
            if model.name == "xgboost":
                eval_set = [(X_val, y_val)]

            model.fit(
                X_train,
                y_train,
                feature_names=feature_names,
                eval_set=eval_set,
            )
            trained.append(TrainedModel(model=model, feature_names=feature_names))
            logger.info("Finished training %s", model.name)

        return trained
