"""End-to-end data pipeline orchestration for Phase 1."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from premonition.config.settings import Settings, get_settings
from premonition.data.loaders import load_dataset, save_processed_splits
from premonition.data.preprocessors import PremonitionPreprocessor
from premonition.data.splitters import DataSplits, SplitConfig, create_splits, extract_xy
from premonition.data.validators import DataQualityReport, validate_dataset
from premonition.features.engineering import engineer_features, select_tier_frame
from premonition.features.feature_registry import FeatureRegistry
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir, timestamp_slug
from premonition.utils.serialization import dumps_json

logger = get_logger(__name__)


@dataclass
class DataPipelineResult:
    """Artifacts produced by the full data pipeline."""

    tier: str
    target_column: str
    feature_columns: list[str]
    quality_report: DataQualityReport
    splits: DataSplits
    preprocessor: PremonitionPreprocessor

    X_train: pd.DataFrame
    X_val: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series

    X_train_processed: np.ndarray
    X_val_processed: np.ndarray
    X_test_processed: np.ndarray

    processed_feature_names: list[str] = field(default_factory=list)
    split_metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "tier": self.tier,
            "target_column": self.target_column,
            "n_features_raw": len(self.feature_columns),
            "n_features_processed": len(self.processed_feature_names),
            "quality_passed": self.quality_report.passed,
            "split_metadata": self.split_metadata,
            "feature_columns": self.feature_columns,
            "processed_feature_names": self.processed_feature_names,
        }


class DataPipeline:
    """
    Orchestrate: load → validate → engineer → tier-select → split → preprocess.

    Usage
    -----
    >>> pipeline = DataPipeline(tier="t1")
    >>> result = pipeline.run()
    >>> result.X_train_processed  # ready for model.fit()
    """

    def __init__(
        self,
        tier: str | None = None,
        settings: Settings | None = None,
        split_config: SplitConfig | None = None,
        raise_on_validation_error: bool = True,
    ) -> None:
        self.settings = settings or get_settings()
        self.tier = (tier or self.settings.primary_tier).lower()
        self.split_config = split_config or SplitConfig.from_model_config(
            self.settings.model_config
        )
        self.raise_on_validation_error = raise_on_validation_error

        self.registry = FeatureRegistry(self.settings.feature_config)
        self.target_column = self.registry.target_column

    def run(
        self,
        dataset_path: Path | str | None = None,
        save_artifacts: bool = True,
    ) -> DataPipelineResult:
        """Execute the complete data pipeline."""
        logger.info("Starting data pipeline (tier=%s)", self.tier)

        # 1. Load
        raw_df = load_dataset(dataset_path, self.settings)

        # 2. Validate raw data
        quality_report = validate_dataset(
            raw_df,
            self.registry,
            raise_on_error=self.raise_on_validation_error,
        )

        # 3. Engineer features
        engineered_df = engineer_features(raw_df, self.registry)

        # 4. Select tier-safe columns
        tier_df = select_tier_frame(engineered_df, self.registry, self.tier)

        # 5. Stratified split (before preprocessing to prevent leakage)
        splits = create_splits(
            tier_df,
            target_column=self.target_column,
            config=self.split_config,
        )

        # 6. Resolve feature column list (exclude id + target)
        feature_columns = [
            c
            for c in tier_df.columns
            if c not in self.registry.identifier_columns
            and c != self.target_column
        ]
        self.registry.validate_no_leakage(feature_columns)

        X_train, y_train = extract_xy(splits.train, feature_columns, self.target_column)
        X_val, y_val = extract_xy(splits.val, feature_columns, self.target_column)
        X_test, y_test = extract_xy(splits.test, feature_columns, self.target_column)

        # 7. Fit preprocessor on train only; transform all splits
        preprocessor = PremonitionPreprocessor(
            registry=self.registry,
            tier=self.tier,
            model_config=self.settings.model_config,
        )
        X_train_processed = preprocessor.fit_transform(X_train, y_train)
        X_val_processed = preprocessor.transform(X_val)
        X_test_processed = preprocessor.transform(X_test)

        result = DataPipelineResult(
            tier=self.tier,
            target_column=self.target_column,
            feature_columns=feature_columns,
            quality_report=quality_report,
            splits=splits,
            preprocessor=preprocessor,
            X_train=X_train,
            X_val=X_val,
            X_test=X_test,
            y_train=y_train,
            y_val=y_val,
            y_test=y_test,
            X_train_processed=X_train_processed,
            X_val_processed=X_val_processed,
            X_test_processed=X_test_processed,
            processed_feature_names=preprocessor.feature_names_out_,
            split_metadata=splits.metadata,
        )

        if save_artifacts:
            self._save_artifacts(result, tier_df)

        logger.info(
            "Pipeline complete - %d raw features -> %d processed features",
            len(feature_columns),
            len(result.processed_feature_names),
        )
        return result

    def _save_artifacts(self, result: DataPipelineResult, tier_df: pd.DataFrame) -> None:
        """Persist splits, quality report, and pipeline metadata."""
        out_dir = ensure_dir(self.settings.data_processed_dir / self.tier)
        stamp = timestamp_slug()

        save_processed_splits(
            {
                "train": result.splits.train,
                "val": result.splits.val,
                "test": result.splits.test,
            },
            out_dir,
        )

        report_path = out_dir / f"quality_report_{stamp}.json"
        report_path.write_text(
            dumps_json(result.quality_report.to_dict()),
            encoding="utf-8",
        )

        meta_path = out_dir / f"pipeline_metadata_{stamp}.json"
        meta_path.write_text(
            dumps_json(result.summary()),
            encoding="utf-8",
        )

        logger.info("Artifacts saved to %s", out_dir)
