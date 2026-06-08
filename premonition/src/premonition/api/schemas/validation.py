"""Input validation helpers for API requests."""

from __future__ import annotations

import pandas as pd

from premonition.api.schemas.errors import ErrorDetail
from premonition.api.schemas.requests import BatchPatientItem, PatientFeaturesRequest
from premonition.features.engineering import engineer_features
from premonition.features.feature_registry import FeatureRegistry


def features_to_dataframe(features: PatientFeaturesRequest) -> pd.DataFrame:
    """Convert a Pydantic feature model to a single-row DataFrame."""
    return pd.DataFrame([features.model_dump()])


def batch_to_dataframe(patients: list[BatchPatientItem]) -> pd.DataFrame:
    """Convert batch request to DataFrame with patient_id column."""
    rows = []
    for p in patients:
        row = p.features.model_dump()
        row["subject_id"] = p.patient_id
        rows.append(row)
    return pd.DataFrame(rows)


def prepare_tier_features(
    df: pd.DataFrame,
    registry: FeatureRegistry,
    tier: str,
) -> pd.DataFrame:
    """
    Engineer and select leakage-safe tier features.

    Raises ValueError with details if validation fails.
    """
    from premonition.features.engineering import select_tier_frame

    engineered = engineer_features(df, registry)
    tier_df = select_tier_frame(engineered, registry, tier, include_missing_indicators=True)
    # Drop target if accidentally present
    target = registry.target_column
    if target in tier_df.columns:
        tier_df = tier_df.drop(columns=[target])
    return tier_df


def validate_tier_columns(
    df: pd.DataFrame,
    registry: FeatureRegistry,
    tier: str,
) -> list[ErrorDetail]:
    """Return validation errors for missing tier columns."""
    from premonition.features.engineering import select_tier_frame

    errors: list[ErrorDetail] = []
    try:
        engineered = engineer_features(df, registry)
        select_tier_frame(engineered, registry, tier)
    except KeyError as exc:
        errors.append(ErrorDetail(field="features", message=str(exc), code="missing_columns"))
    return errors
