"""Leakage-safe feature engineering for early-warning tiers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from premonition.features.feature_registry import FeatureRegistry
from premonition.utils.logging import get_logger

logger = get_logger(__name__)

_COMORBIDITY_COLUMNS = [
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
]


def clean_gender(df: pd.DataFrame) -> pd.DataFrame:
    """Fix known data entry errors in gender column."""
    out = df.copy()
    if "gender" not in out.columns:
        return out

    mapping = {"Mael": "M", "mael": "M", "Male": "M", "Female": "F"}
    out["gender"] = out["gender"].replace(mapping)
    return out


def compute_bmi_if_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Derive BMI from weight/height when BMI is null."""
    out = df.copy()
    if "bmi" not in out.columns:
        return out

    mask = out["bmi"].isna() & out["weight_kg"].notna() & out["height_cm"].notna()
    if mask.any():
        height_m = out.loc[mask, "height_cm"] / 100.0
        out.loc[mask, "bmi"] = out.loc[mask, "weight_kg"] / (height_m ** 2)
        logger.info("Derived BMI for %d rows", int(mask.sum()))
    return out


def engineer_features(
    df: pd.DataFrame,
    registry: FeatureRegistry | None = None,
) -> pd.DataFrame:
    """
    Add engineered early-warning features to the dataframe.

    All features use only safe T0/T1 inputs — no labs, no severity scores,
    no intervention flags.

    Engineered columns
    ------------------
    comorbidity_count   : sum of 10 comorbidity binary flags
    shock_index         : hr_mean / sbp_mean  (hemodynamic stress)
    pulse_pressure      : sbp_mean - dbp_mean
    hr_range            : hr_max - hr_min
    sbp_range           : sbp_max - sbp_min
    temp_range          : temp_celsius_max - temp_celsius_min
    spo2_range          : spo2_max - spo2_min
    respiratory_rate_range : respiratory_rate_max - respiratory_rate_min
    """
    out = clean_gender(df)
    out = compute_bmi_if_missing(out)

    out["comorbidity_count"] = _safe_sum_flags(out, _COMORBIDITY_COLUMNS)

    if _has_columns(out, "hr_mean", "sbp_mean"):
        out["shock_index"] = _safe_divide(out["hr_mean"], out["sbp_mean"])

    if _has_columns(out, "sbp_mean", "dbp_mean"):
        out["pulse_pressure"] = out["sbp_mean"] - out["dbp_mean"]

    out["hr_range"] = _safe_range(out, "hr_max", "hr_min")
    out["sbp_range"] = _safe_range(out, "sbp_max", "sbp_min")
    out["temp_range"] = _safe_range(out, "temp_celsius_max", "temp_celsius_min")
    out["spo2_range"] = _safe_range(out, "spo2_max", "spo2_min")
    out["respiratory_rate_range"] = _safe_range(
        out, "respiratory_rate_max", "respiratory_rate_min"
    )

    if registry is not None:
        registry.validate_no_leakage(
            [c for c in out.columns if c in registry.engineered_columns]
        )

    logger.info("Engineered %d derived features", len(registry.engineered_columns) if registry else 8)
    return out


def add_missing_indicators(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Add binary `{column}_missing` flags for lab columns (T2 tier).

    Indicators are computed before imputation so the model can learn
    MNAR patterns (labs missing more often in sicker patients).
    """
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            continue
        indicator = f"{col}_missing"
        out[indicator] = out[col].isna().astype(np.int8)
    return out


def select_tier_frame(
    df: pd.DataFrame,
    registry: FeatureRegistry,
    tier: str,
    include_missing_indicators: bool = True,
) -> pd.DataFrame:
    """
    Select only leakage-safe columns for a given tier.

    Returns dataframe with tier features + subject_id + target (if present).
    """
    tier = tier.lower()
    feature_cols = registry.get_tier_columns(tier)
    registry.validate_no_leakage(feature_cols)

    working = df.copy()
    if tier == "t2" and include_missing_indicators:
        working = add_missing_indicators(working, registry.lab_columns)
        feature_cols = feature_cols + registry.get_missing_indicator_columns(tier)

    keep = list(registry.identifier_columns) + feature_cols
    if registry.target_column in working.columns:
        keep.append(registry.target_column)

    missing_cols = [c for c in keep if c not in working.columns]
    if missing_cols:
        raise KeyError(f"Tier '{tier}' requires missing columns: {missing_cols}")

    return working[keep].copy()


def _has_columns(df: pd.DataFrame, *cols: str) -> bool:
    return all(c in df.columns for c in cols)


def _safe_sum_flags(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    present = [c for c in columns if c in df.columns]
    if not present:
        return pd.Series(0, index=df.index, dtype=float)
    return df[present].fillna(0).sum(axis=1)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denom = denominator.replace(0, np.nan)
    return numerator / denom


def _safe_range(df: pd.DataFrame, max_col: str, min_col: str) -> pd.Series:
    if not _has_columns(df, max_col, min_col):
        return pd.Series(np.nan, index=df.index, dtype=float)
    return df[max_col] - df[min_col]
