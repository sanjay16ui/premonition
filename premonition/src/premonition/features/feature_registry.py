"""Central registry for leakage-safe feature columns by tier."""

from __future__ import annotations

from typing import Any


class FeatureRegistry:
    """Resolve feature column lists from feature_tiers.yaml."""

    def __init__(self, feature_config: dict[str, Any]) -> None:
        self._cfg = feature_config

    @property
    def target_column(self) -> str:
        return self._cfg["target"]["primary"]

    @property
    def identifier_columns(self) -> list[str]:
        return list(self._cfg.get("identifier", []))

    @property
    def excluded_columns(self) -> list[str]:
        """All columns that must never enter the model."""
        groups = (
            "excluded_leakage",
            "excluded_interventions",
            "excluded_outcome_adjacent",
        )
        excluded: list[str] = []
        for group in groups:
            excluded.extend(self._cfg.get(group, []))
        excluded.extend(self._cfg["target"]["exclude_from_features"])
        return sorted(set(excluded))

    @property
    def categorical_columns(self) -> list[str]:
        return list(self._cfg.get("categorical", []))

    @property
    def lab_columns(self) -> list[str]:
        return list(self._cfg.get("tier_t2_labs", []))

    @property
    def engineered_columns(self) -> list[str]:
        return list(self._cfg.get("engineered", []))

    def _base_columns(self) -> list[str]:
        """T0 raw columns (demographics + comorbidities + admin)."""
        return (
            list(self._cfg.get("tier_t0_demographics", []))
            + list(self._cfg.get("tier_t0_comorbidities", []))
            + list(self._cfg.get("tier_t0_admin", []))
        )

    def _vital_columns(self) -> list[str]:
        return list(self._cfg.get("tier_t1_vitals", []))

    def tier_engineered_columns(self, tier: str) -> list[str]:
        """Engineered features enabled for a given tier."""
        tier_cfg = self._cfg.get("tiers", {}).get(tier, {})
        return list(tier_cfg.get("includes_engineered", []))

    def get_tier_columns(self, tier: str) -> list[str]:
        """
        Return ordered, deduplicated safe feature columns for a tier.

        t0: demographics + comorbidities + admin + tier engineered
        t1: t0 + vitals + tier engineered
        t2: t1 + labs + tier engineered (+ missing indicators added at preprocess time)
        """
        tier = tier.lower()
        if tier not in {"t0", "t1", "t2"}:
            raise ValueError(f"Unknown tier '{tier}'. Expected t0, t1, or t2.")

        columns: list[str] = self._base_columns()
        if tier in {"t1", "t2"}:
            columns.extend(self._vital_columns())
        if tier == "t2":
            columns.extend(self.lab_columns)

        columns.extend(self.tier_engineered_columns(tier))

        # Preserve order, remove duplicates
        seen: set[str] = set()
        ordered: list[str] = []
        for col in columns:
            if col not in seen:
                seen.add(col)
                ordered.append(col)
        return ordered

    def get_missing_indicator_columns(self, tier: str) -> list[str]:
        """Binary missing flags — only for T2 lab columns."""
        if tier.lower() != "t2":
            return []
        return [f"{col}_missing" for col in self.lab_columns]

    def validate_no_leakage(self, columns: list[str]) -> None:
        """Raise if any excluded or target column appears in the feature list."""
        forbidden = set(self.excluded_columns) | {self.target_column}
        leaked = sorted(set(columns) & forbidden)
        if leaked:
            raise ValueError(
                f"Leakage detected: forbidden columns in feature set: {leaked}"
            )

    def all_raw_columns(self) -> list[str]:
        """Every column expected in the raw CSV (for schema validation).

        Engineered columns are computed at runtime and are not required in raw data.
        """
        raw_t2 = (
            self._base_columns()
            + self._vital_columns()
            + self.lab_columns
        )
        return sorted(
            set(
                self.identifier_columns
                + raw_t2
                + self.excluded_columns
                + [self.target_column, "readmission_30day"]
            )
        )
