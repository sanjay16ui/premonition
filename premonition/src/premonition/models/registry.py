"""Model persistence — save and load trained models + versioned metadata."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

from premonition.data.preprocessors import PremonitionPreprocessor
from premonition.models.base import BaseModelWrapper
from premonition.models.versioning import build_model_version_record
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir, timestamp_slug
from premonition.utils.serialization import dumps_json

logger = get_logger(__name__)


@dataclass
class ModelArtifact:
    """Paths and metadata for one saved model bundle."""

    model_name: str
    tier: str
    model_path: Path
    preprocessor_path: Path | None
    metrics_path: Path
    metadata_path: Path
    version_path: Path | None = None
    is_best: bool = False


class ModelRegistry:
    """
    Save and load model artifacts to disk.

    Each model bundle contains:
    - model.joblib          — trained estimator
    - preprocessor.joblib   — fitted Section 3 preprocessor
    - metrics.json          — evaluation metrics
    - metadata.json         — tier, feature names, selection info
    """

    def __init__(self, models_dir: Path) -> None:
        self.models_dir = ensure_dir(models_dir)

    def save_model(
        self,
        model: BaseModelWrapper,
        tier: str,
        metrics: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        preprocessor: PremonitionPreprocessor | None = None,
        is_best: bool = False,
        stamp: str | None = None,
        dataset_path: Path | None = None,
    ) -> ModelArtifact:
        """
        Persist a trained model with full version tracking.

        Saved files per bundle
        ----------------------
        - model.joblib       — trained estimator
        - preprocessor.joblib — fitted preprocessor (best model only)
        - metrics.json       — validation/test metrics
        - metadata.json      — runtime metadata
        - version.json       — model version, dataset version, feature set
        """
        stamp = stamp or timestamp_slug()
        training_ts = datetime.now(timezone.utc).isoformat()
        bundle_dir = ensure_dir(self.models_dir / tier / f"{model.name}_{stamp}")
        if is_best:
            bundle_dir = ensure_dir(self.models_dir / tier / "best_model")

        model_path = bundle_dir / "model.joblib"
        joblib.dump(model, model_path)

        preprocessor_path = None
        if preprocessor is not None:
            preprocessor_path = bundle_dir / "preprocessor.joblib"
            joblib.dump(preprocessor, preprocessor_path)

        metrics_path = bundle_dir / "metrics.json"
        metrics_path.write_text(dumps_json(metrics), encoding="utf-8")

        ds_path = dataset_path or Path("dataset.csv")
        version_record = build_model_version_record(
            model_name=model.name,
            tier=tier,
            feature_names=model.feature_names_,
            metrics=metrics,
            dataset_path=ds_path,
            training_timestamp=training_ts,
            extra={"is_best": is_best, "artifact_stamp": stamp},
        )
        version_path = bundle_dir / "version.json"
        version_path.write_text(dumps_json(version_record), encoding="utf-8")

        full_metadata = {
            "model_name": model.name,
            "tier": tier,
            "is_best": is_best,
            "model_version": version_record["model_version"],
            "training_timestamp": training_ts,
            "feature_names": model.feature_names_,
            "feature_set": model.feature_names_,
            "is_fitted": model.is_fitted,
            **(metadata or {}),
        }
        metadata_path = bundle_dir / "metadata.json"
        metadata_path.write_text(dumps_json(full_metadata), encoding="utf-8")

        logger.info("Saved model '%s' v%s -> %s", model.name, version_record["model_version"], bundle_dir)
        return ModelArtifact(
            model_name=model.name,
            tier=tier,
            model_path=model_path,
            preprocessor_path=preprocessor_path,
            metrics_path=metrics_path,
            metadata_path=metadata_path,
            version_path=version_path,
            is_best=is_best,
        )

    def load_model(self, path: Path) -> BaseModelWrapper:
        """Load a saved model wrapper from disk."""
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}")
        model = joblib.load(path)
        logger.info("Loaded model from %s", path)
        return model

    def load_best_model(self, tier: str) -> BaseModelWrapper:
        """Load the best model for a given tier."""
        path = self.models_dir / tier / "best_model" / "model.joblib"
        return self.load_model(path)

    def load_preprocessor(self, tier: str) -> PremonitionPreprocessor:
        """Load the preprocessor saved alongside the best model."""
        path = self.models_dir / tier / "best_model" / "preprocessor.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Preprocessor not found: {path}")
        return joblib.load(path)

    def load_metadata(self, tier: str) -> dict[str, Any]:
        """Load metadata.json for the best model."""
        path = self.models_dir / tier / "best_model" / "metadata.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def load_version(self, tier: str) -> dict[str, Any]:
        """Load version.json for the best model."""
        path = self.models_dir / tier / "best_model" / "version.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def list_models(self, tier: str) -> list[dict[str, Any]]:
        """List all saved model bundles for a tier."""
        tier_dir = self.models_dir / tier
        if not tier_dir.exists():
            return []

        bundles = []
        for bundle_path in sorted(tier_dir.iterdir()):
            version_file = bundle_path / "version.json"
            if version_file.exists():
                bundles.append(json.loads(version_file.read_text(encoding="utf-8")))
        return bundles
