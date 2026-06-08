"""Analyse why a patient's sepsis risk increased or decreased."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from premonition.explainability.feature_labels import categorize_feature, friendly_name
from premonition.explainability.shap_explainer import ShapExplanation


@dataclass
class RiskAnalysis:
    """
    Structured breakdown of what drove a patient's risk score.

    Answers three clinical questions:
    1. What pushed risk UP?
    2. What pushed risk DOWN?
    3. Which clinical category matters most?
    """

    risk_increasers: list[dict[str, Any]] = field(default_factory=list)
    risk_decreasers: list[dict[str, Any]] = field(default_factory=list)
    category_impact: dict[str, float] = field(default_factory=dict)
    dominant_category: str = ""
    net_direction: str = ""     # "increasing" | "decreasing" | "mixed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_increasers": self.risk_increasers,
            "risk_decreasers": self.risk_decreasers,
            "category_impact": self.category_impact,
            "dominant_category": self.dominant_category,
            "net_direction": self.net_direction,
        }


class RiskAnalyzer:
    """
    Interpret SHAP values to explain risk direction.

    Think of SHAP like a receipt:
    - Each line item (feature) added or subtracted from the bill (risk score).
    - Positive SHAP = feature added to the bill (risk went UP).
    - Negative SHAP = feature gave a discount (risk went DOWN).
    """

    def analyze(
        self,
        explanation: ShapExplanation,
        patient_index: int,
        top_n: int = 5,
    ) -> RiskAnalysis:
        """Analyse one patient's SHAP values."""
        shap_vals = explanation.local_values(patient_index)
        pcts = explanation.contribution_pct(patient_index)

        increasers: list[dict[str, Any]] = []
        decreasers: list[dict[str, Any]] = []
        category_totals: dict[str, float] = {}

        for feat, val in shap_vals.items():
            cat = categorize_feature(feat)
            category_totals[cat] = category_totals.get(cat, 0.0) + abs(val)

            entry = {
                "feature": feat,
                "display_name": friendly_name(feat),
                "shap_value": round(val, 4),
                "contribution_pct": round(pcts.get(feat, 0.0), 1),
                "category": cat,
            }
            if val > 0:
                increasers.append(entry)
            elif val < 0:
                decreasers.append(entry)

        increasers.sort(key=lambda x: x["contribution_pct"], reverse=True)
        decreasers.sort(key=lambda x: x["contribution_pct"], reverse=True)

        dominant = max(category_totals, key=category_totals.get) if category_totals else ""
        total_positive = sum(v for v in shap_vals.values() if v > 0)
        total_negative = abs(sum(v for v in shap_vals.values() if v < 0))

        if total_positive > total_negative * 1.5:
            net = "increasing"
        elif total_negative > total_positive * 1.5:
            net = "decreasing"
        else:
            net = "mixed"

        return RiskAnalysis(
            risk_increasers=increasers[:top_n],
            risk_decreasers=decreasers[:top_n],
            category_impact={k: round(v, 4) for k, v in category_totals.items()},
            dominant_category=dominant,
            net_direction=net,
        )
