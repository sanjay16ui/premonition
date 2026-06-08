"""Feature registry and engineering for early-warning tiers."""

from premonition.features.engineering import (
    add_missing_indicators,
    clean_gender,
    compute_bmi_if_missing,
    engineer_features,
    select_tier_frame,
)
from premonition.features.feature_registry import FeatureRegistry

__all__ = [
    "FeatureRegistry",
    "add_missing_indicators",
    "clean_gender",
    "compute_bmi_if_missing",
    "engineer_features",
    "select_tier_frame",
]
