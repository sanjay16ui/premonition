"""Cohort analysis engine."""

from __future__ import annotations

from typing import Any

import pandas as pd

from premonition.analytics.schemas import CohortAnalysisRequest, CohortSegment
from premonition.features.engineering import engineer_features
from premonition.features.feature_registry import FeatureRegistry


class CohortAnalysisEngine:
    """Segment patient populations for comparative analysis."""

    SEGMENT_COLUMNS = {
        "age_group": "age",
        "gender": "gender",
        "ethnicity": "ethnicity",
        "comorbidity": "comorbidity_count",
        "admit_source": "hospital_admit_source",
    }

    def analyze(
        self,
        df: pd.DataFrame,
        request: CohortAnalysisRequest,
        target_col: str = "sepsis_label",
        feature_config: dict | None = None,
    ) -> list[CohortSegment]:
        working = df.copy()
        col = self.SEGMENT_COLUMNS.get(request.segment_by, request.segment_by)
        if col not in working.columns and feature_config:
            registry = FeatureRegistry(feature_config)
            working = engineer_features(working, registry)

        if col not in working.columns:
            return []

        filtered = self._apply_filters(working, request.filters)
        segments: list[CohortSegment] = []

        if request.segment_by == "age_group" and col == "age":
            groups = self._age_cohorts(filtered)
        elif request.segment_by == "comorbidity" and col == "comorbidity_count":
            groups = self._comorbidity_cohorts(filtered)
        else:
            groups = {str(k): filtered[filtered[col] == k] for k in filtered[col].unique()}

        for name, subset in groups.items():
            if len(subset) == 0:
                continue
            sepsis_rate = float(subset[target_col].mean()) if target_col in subset.columns else 0.0
            avg_risk = float(subset.get("risk_score", pd.Series([0.0])).mean())
            factors = self._top_risk_factors(subset)
            segments.append(CohortSegment(
                name=str(name),
                size=len(subset),
                sepsis_rate=round(sepsis_rate, 4),
                avg_risk_score=round(avg_risk, 4),
                mortality_proxy=round(sepsis_rate * 0.3, 4),
                top_risk_factors=factors,
            ))
        segments.sort(key=lambda s: s.sepsis_rate, reverse=True)
        return segments

    def _apply_filters(self, df: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
        result = df.copy()
        for key, value in filters.items():
            if key in result.columns:
                result = result[result[key] == value]
        return result

    def _age_cohorts(self, df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        bins = [0, 50, 65, 80, 200]
        labels = ["young", "middle", "elderly", "very_elderly"]
        df = df.copy()
        df["_cohort"] = pd.cut(df["age"], bins=bins, labels=labels, right=False)
        return {str(k): df[df["_cohort"] == k] for k in labels}

    def _comorbidity_cohorts(self, df: pd.DataFrame) -> dict[str, pd.DataFrame]:
        df = df.copy()
        df["_cohort"] = pd.cut(
            df["comorbidity_count"], bins=[-1, 0, 2, 5, 20], labels=["none", "low", "moderate", "high"],
        )
        return {str(k): df[df["_cohort"] == k] for k in ["none", "low", "moderate", "high"]}

    def _top_risk_factors(self, df: pd.DataFrame) -> list[str]:
        vitals = ["hr_mean", "spo2_mean", "temp_celsius_mean", "map_mean", "respiratory_rate_mean"]
        factors = []
        for v in vitals:
            if v in df.columns and df[v].mean() != df[v].median():
                factors.append(v.replace("_mean", ""))
        return factors[:5] or ["vitals", "comorbidities"]
