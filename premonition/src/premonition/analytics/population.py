"""Population health analytics."""

from __future__ import annotations

from typing import Any

import pandas as pd

from premonition.analytics.schemas import PopulationAnalytics


class PopulationHealthAnalytics:
    """Population-level sepsis incidence and risk analytics."""

    def analyze(self, df: pd.DataFrame, target_col: str = "sepsis_label") -> PopulationAnalytics:
        total = len(df)
        sepsis_rate = float(df[target_col].mean()) if target_col in df.columns else 0.0

        risk_dist = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
        if "risk_score" in df.columns:
            for score in df["risk_score"]:
                if score < 0.15:
                    risk_dist["low"] += 1
                elif score < 0.35:
                    risk_dist["moderate"] += 1
                elif score < 0.55:
                    risk_dist["high"] += 1
                else:
                    risk_dist["critical"] += 1

        demographics: dict[str, Any] = {}
        if "age" in df.columns:
            demographics["age"] = {
                "mean": round(float(df["age"].mean()), 1),
                "median": round(float(df["age"].median()), 1),
                "groups": self._age_groups(df),
            }
        if "gender" in df.columns:
            demographics["gender"] = df["gender"].value_counts().to_dict()
        if "ethnicity" in df.columns:
            demographics["ethnicity"] = df["ethnicity"].value_counts().head(5).to_dict()

        trend = self._incidence_trend(df, target_col)
        return PopulationAnalytics(
            total_patients=total,
            sepsis_incidence=round(sepsis_rate, 4),
            risk_distribution=risk_dist,
            demographic_breakdown=demographics,
            trend=trend,
        )

    def _age_groups(self, df: pd.DataFrame) -> dict[str, int]:
        bins = [0, 40, 60, 75, 200]
        labels = ["<40", "40-59", "60-74", "75+"]
        groups = pd.cut(df["age"], bins=bins, labels=labels, right=False)
        return {str(k): int(v) for k, v in groups.value_counts().items()}

    def _incidence_trend(self, df: pd.DataFrame, target_col: str) -> list[dict[str, Any]]:
        if target_col not in df.columns or len(df) < 50:
            return []
        chunk = max(len(df) // 5, 10)
        trend = []
        for i in range(0, len(df), chunk):
            subset = df.iloc[i:i + chunk]
            trend.append({
                "segment": i // chunk + 1,
                "n": len(subset),
                "sepsis_rate": round(float(subset[target_col].mean()), 4),
            })
        return trend
