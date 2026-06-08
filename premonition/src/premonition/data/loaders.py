"""Dataset loading utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from premonition.config.settings import Settings, get_settings
from premonition.utils.logging import get_logger

logger = get_logger(__name__)

# Expected binary flag columns (0/1 integers)
_BINARY_COLUMNS = [
    "diabetes",
    "hypertension",
    "chf",
    "copd",
    "chronic_kidney_disease",
    "liver_disease",
    "immunosuppression",
    "cad",
    "atrial_fibrillation",
    "cancer_active",
    "sepsis_label",
    "readmission_30day",
]

# Expected categorical columns
_CATEGORICAL_COLUMNS = [
    "gender",
    "ethnicity",
    "insurance",
    "hospital_admit_source",
]


def load_dataset(
    path: Path | str | None = None,
    settings: Settings | None = None,
) -> pd.DataFrame:
    """
    Load the raw ICU dataset from CSV.

    Parameters
    ----------
    path:
        Optional override path. Defaults to settings.dataset_path.
    settings:
        Optional settings instance.

    Returns
    -------
    pd.DataFrame
        Raw dataframe with coerced dtypes.
    """
    cfg = settings or get_settings()
    dataset_path = Path(path) if path else cfg.dataset_path

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    logger.info("Loading dataset from %s", dataset_path)
    df = pd.read_csv(dataset_path)

    df = _coerce_dtypes(df)
    logger.info("Loaded %d rows × %d columns", df.shape[0], df.shape[1])
    return df


def _coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Apply consistent dtypes after CSV parse."""
    out = df.copy()

    if "subject_id" in out.columns:
        out["subject_id"] = out["subject_id"].astype("int64")

    for col in _BINARY_COLUMNS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")

    for col in _CATEGORICAL_COLUMNS:
        if col in out.columns:
            out[col] = out[col].astype("string")

    int_cols = ["age", "icu_admit_time_hour", "day_of_week"]
    for col in int_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")

    return out


def save_processed_splits(
    splits: dict[str, pd.DataFrame],
    output_dir: Path,
) -> None:
    """Persist train/val/test parquet splits to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in splits.items():
        out_path = output_dir / f"{name}.parquet"
        frame.to_parquet(out_path, index=False)
        logger.info("Saved %s (%d rows) -> %s", name, len(frame), out_path)
