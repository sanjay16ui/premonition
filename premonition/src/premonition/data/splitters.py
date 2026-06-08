"""Stratified train / validation / test splitting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from sklearn.model_selection import train_test_split

from premonition.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SplitConfig:
    """Split proportions and reproducibility settings."""

    test_size: float = 0.10
    val_size: float = 0.10
    random_state: int = 42
    stratify: bool = True

    @classmethod
    def from_model_config(cls, model_config: dict[str, Any]) -> SplitConfig:
        split_cfg = model_config.get("split", {})
        return cls(
            test_size=float(split_cfg.get("test_size", 0.10)),
            val_size=float(split_cfg.get("val_size", 0.10)),
            random_state=int(split_cfg.get("random_state", 42)),
            stratify=bool(split_cfg.get("stratify", True)),
        )


@dataclass
class DataSplits:
    """Container for stratified train/val/test partitions."""

    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    target_column: str

    @property
    def metadata(self) -> dict[str, Any]:
        def _split_stats(df: pd.DataFrame) -> dict[str, Any]:
            y = df[self.target_column]
            return {
                "n_rows": len(df),
                "positive_rate": float(y.mean()),
                "n_positive": int(y.sum()),
                "n_negative": int((y == 0).sum()),
            }

        return {
            "train": _split_stats(self.train),
            "val": _split_stats(self.val),
            "test": _split_stats(self.test),
        }


def create_splits(
    df: pd.DataFrame,
    target_column: str,
    config: SplitConfig | None = None,
    model_config: dict[str, Any] | None = None,
) -> DataSplits:
    """
    Create stratified 80/10/10 train/val/test splits.

    Split strategy
    --------------
    1. Hold out `test_size` (10%) as test set.
    2. From remaining 90%, hold out val proportion to achieve `val_size` (10%) overall.
       val_fraction_of_remainder = val_size / (1 - test_size) = 0.10 / 0.90 ≈ 0.1111

    Parameters
    ----------
    df:
        Full tier-selected dataframe (must include target).
    target_column:
        Binary target column name.
    config:
        Optional explicit split config.
    model_config:
        Optional model_config dict (used if config is None).

    Returns
    -------
    DataSplits
    """
    if config is None:
        config = SplitConfig.from_model_config(model_config or {})

    if target_column not in df.columns:
        raise KeyError(f"Target column '{target_column}' not in dataframe")

    y = df[target_column]
    stratify = y if config.stratify else None

    # Step 1: train+val vs test
    train_val, test = train_test_split(
        df,
        test_size=config.test_size,
        random_state=config.random_state,
        stratify=stratify,
    )

    # Step 2: train vs val from remainder
    val_fraction = config.val_size / (1.0 - config.test_size)
    stratify_tv = train_val[target_column] if config.stratify else None

    train, val = train_test_split(
        train_val,
        test_size=val_fraction,
        random_state=config.random_state,
        stratify=stratify_tv,
    )

    splits = DataSplits(
        train=train.reset_index(drop=True),
        val=val.reset_index(drop=True),
        test=test.reset_index(drop=True),
        target_column=target_column,
    )

    meta = splits.metadata
    logger.info(
        "Splits created — train=%d (%.1f%% pos), val=%d (%.1f%% pos), test=%d (%.1f%% pos)",
        meta["train"]["n_rows"],
        meta["train"]["positive_rate"] * 100,
        meta["val"]["n_rows"],
        meta["val"]["positive_rate"] * 100,
        meta["test"]["n_rows"],
        meta["test"]["positive_rate"] * 100,
    )
    return splits


def extract_xy(
    df: pd.DataFrame,
    feature_columns: list[str],
    target_column: str,
) -> tuple[pd.DataFrame, pd.Series]:
    """Separate features and target from a split dataframe."""
    X = df[feature_columns].copy()
    y = df[target_column].astype(int)
    return X, y
