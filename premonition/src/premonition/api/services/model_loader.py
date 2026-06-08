"""Model loading service — startup model + preprocessor initialization."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np

from premonition.config.settings import Settings
from premonition.data.pipeline import DataPipeline
from premonition.data.preprocessors import PremonitionPreprocessor
from premonition.features.feature_registry import FeatureRegistry
from premonition.intelligence.predictor import PredictionIntelligence
from premonition.models.base import BaseModelWrapper
from premonition.models.registry import ModelRegistry
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ModelState:
    """Runtime state for loaded ML artifacts."""

    loaded: bool = False
    model: BaseModelWrapper | None = None
    preprocessor: PremonitionPreprocessor | None = None
    intelligence: PredictionIntelligence | None = None
    registry: ModelRegistry | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    version_info: dict[str, Any] = field(default_factory=dict)
    tier: str = "t1"
    loaded_at: str | None = None
    background_data: np.ndarray | None = None
    feature_registry: FeatureRegistry | None = None
    load_error: str | None = None


class ModelLoaderService:
    """
    Load and manage ML model lifecycle for the API.

    Called once at application startup (lifespan).
    Automatically loads best_model from registry + preprocessor.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.state = ModelState(tier=settings.primary_tier)

    async def load(self) -> ModelState:
        """Load model artifacts asynchronously (CPU-bound work in thread)."""
        return await asyncio.to_thread(self._load_sync)

    def _load_sync(self) -> ModelState:
        try:
            registry = ModelRegistry(self.settings.models_dir)
            intelligence = PredictionIntelligence(
                tier=self.settings.primary_tier,
                settings=self.settings,
                log_predictions=True,
            )
            intelligence.load()

            # Set SHAP background from training data sample
            try:
                data = DataPipeline(
                    tier=self.settings.primary_tier,
                    settings=self.settings,
                ).run(save_artifacts=False)
                intelligence.set_background(data.X_train_processed)
                self.state.background_data = data.X_train_processed
            except Exception as bg_exc:
                logger.warning("Could not set SHAP background: %s", bg_exc)

            self.state.registry = registry
            self.state.intelligence = intelligence
            self.state.model = intelligence.model
            self.state.preprocessor = intelligence.preprocessor
            self.state.metadata = registry.load_metadata(self.settings.primary_tier)
            self.state.version_info = registry.load_version(self.settings.primary_tier)
            self.state.feature_registry = FeatureRegistry(self.settings.feature_config)
            self.state.loaded = True
            self.state.loaded_at = datetime.now(timezone.utc).isoformat()
            self.state.load_error = None

            logger.info(
                "Model loaded: %s v%s (tier=%s)",
                self.state.model.name if self.state.model else "?",
                self.state.metadata.get("model_version", "?"),
                self.settings.primary_tier,
            )
        except Exception as exc:
            self.state.loaded = False
            self.state.load_error = str(exc)
            logger.error("Model loading failed: %s", exc)

        return self.state

    def is_ready(self) -> bool:
        return self.state.loaded and self.state.model is not None

    def get_version_info(self) -> dict[str, Any]:
        if not self.state.version_info:
            return {
                "model_name": self.state.metadata.get("model_name", "unknown"),
                "model_version": self.state.metadata.get("model_version", "unknown"),
                "tier": self.state.tier,
            }
        return self.state.version_info
