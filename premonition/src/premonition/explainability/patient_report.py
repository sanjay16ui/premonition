"""Patient-level prediction explanation reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from premonition.explainability.feature_labels import categorize_feature, friendly_name
from premonition.explainability.shap_explainer import ShapExplanation
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir
from premonition.utils.serialization import dumps_json

logger = get_logger(__name__)


@dataclass
class ContributingFactor:
    """One feature's contribution to a patient's risk score."""

    feature: str
    display_name: str
    shap_value: float
    contribution_pct: float
    direction: str          # "increased" | "decreased"
    category: str


@dataclass
class PatientExplanationReport:
    """
    Full explanation report for a single patient prediction.

    Example output
    --------------
    Patient ID: 204
    Predicted Sepsis Risk: 91%
    Top Contributing Factors:
      1. Shock Index (+24%)
      2. Heart Rate Variability (+18%)
    Prediction Confidence: High
    """

    patient_id: int | str
    risk_score: float
    prediction: int
    confidence: str
    top_factors: list[ContributingFactor]
    risk_increasers: list[ContributingFactor] = field(default_factory=list)
    risk_decreasers: list[ContributingFactor] = field(default_factory=list)
    model_name: str = ""
    explanation_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "risk_score": round(self.risk_score, 4),
            "risk_pct": f"{self.risk_score * 100:.0f}%",
            "prediction": self.prediction,
            "prediction_label": "Sepsis Risk" if self.prediction == 1 else "No Sepsis",
            "confidence": self.confidence,
            "model_name": self.model_name,
            "top_factors": [
                {
                    "rank": i + 1,
                    "feature": f.display_name,
                    "contribution_pct": round(f.contribution_pct, 1),
                    "direction": f.direction,
                    "shap_value": round(f.shap_value, 4),
                    "category": f.category,
                }
                for i, f in enumerate(self.top_factors)
            ],
            "risk_increasers": [f.display_name for f in self.risk_increasers[:5]],
            "risk_decreasers": [f.display_name for f in self.risk_decreasers[:5]],
            "explanation_summary": self.explanation_summary,
        }

    def to_text(self) -> str:
        """Human-readable report for clinicians."""
        lines = [
            f"Patient ID: {self.patient_id}",
            f"Predicted Sepsis Risk: {self.risk_score * 100:.0f}%",
            f"Prediction: {'SEPSIS ALERT' if self.prediction == 1 else 'No Alert'}",
            f"Prediction Confidence: {self.confidence}",
            "",
            "Top Contributing Factors:",
        ]
        for i, factor in enumerate(self.top_factors, start=1):
            sign = "+" if factor.direction == "increased" else "-"
            lines.append(
                f"  {i}. {factor.display_name} ({sign}{factor.contribution_pct:.0f}%)"
            )

        if self.risk_increasers:
            lines.append("")
            lines.append("Why risk INCREASED:")
            for f in self.risk_increasers[:3]:
                lines.append(f"  - {f.display_name} pushed risk up")

        if self.risk_decreasers:
            lines.append("")
            lines.append("Why risk DECREASED:")
            for f in self.risk_decreasers[:3]:
                lines.append(f"  - {f.display_name} pushed risk down")

        lines.append("")
        lines.append(f"Summary: {self.explanation_summary}")
        return "\n".join(lines)


class PatientReportGenerator:
    """Build patient-level explanation reports from SHAP values."""

    def __init__(self, top_n: int = 5) -> None:
        self.top_n = top_n

    def generate(
        self,
        patient_id: int | str,
        patient_index: int,
        risk_score: float,
        prediction: int,
        confidence: str,
        explanation: ShapExplanation,
        model_name: str = "",
    ) -> PatientExplanationReport:
        """Create a full explanation report for one patient."""
        shap_vals = explanation.local_values(patient_index)
        pcts = explanation.contribution_pct(patient_index)

        factors: list[ContributingFactor] = []
        for feat, shap_val in shap_vals.items():
            factors.append(
                ContributingFactor(
                    feature=feat,
                    display_name=friendly_name(feat),
                    shap_value=shap_val,
                    contribution_pct=pcts.get(feat, 0.0),
                    direction="increased" if shap_val > 0 else "decreased",
                    category=categorize_feature(feat),
                )
            )

        # Top factors by absolute contribution %
        top = sorted(factors, key=lambda f: f.contribution_pct, reverse=True)[: self.top_n]
        increasers = sorted(
            [f for f in factors if f.shap_value > 0],
            key=lambda f: f.contribution_pct,
            reverse=True,
        )
        decreasers = sorted(
            [f for f in factors if f.shap_value < 0],
            key=lambda f: f.contribution_pct,
            reverse=True,
        )

        summary = self._build_summary(risk_score, top, increasers, decreasers)

        return PatientExplanationReport(
            patient_id=patient_id,
            risk_score=risk_score,
            prediction=prediction,
            confidence=confidence,
            top_factors=top,
            risk_increasers=increasers,
            risk_decreasers=decreasers,
            model_name=model_name or explanation.model_name,
            explanation_summary=summary,
        )

    def _build_summary(
        self,
        risk_score: float,
        top: list[ContributingFactor],
        increasers: list[ContributingFactor],
        decreasers: list[ContributingFactor],
    ) -> str:
        """One-sentence narrative for audit logs and dashboards."""
        risk_pct = risk_score * 100
        if not top:
            return f"Patient has {risk_pct:.0f}% sepsis risk with no dominant contributing factors."

        main_factor = top[0].display_name
        if risk_score >= 0.6:
            return (
                f"High sepsis risk ({risk_pct:.0f}%) primarily driven by "
                f"{main_factor} and {len(increasers)} other risk-increasing factors."
            )
        if risk_score >= 0.35:
            return (
                f"Moderate sepsis risk ({risk_pct:.0f}%) influenced by "
                f"{main_factor}, with {len(decreasers)} protective factors partially offsetting."
            )
        return (
            f"Low sepsis risk ({risk_pct:.0f}%). "
            f"{decreasers[0].display_name if decreasers else main_factor} "
            f"is the strongest protective signal."
        )

    def save_report(
        self,
        report: PatientExplanationReport,
        output_dir: Path,
    ) -> tuple[Path, Path]:
        """Save report as JSON and plain-text."""
        ensure_dir(output_dir)
        pid = str(report.patient_id)
        json_path = output_dir / f"patient_{pid}_explanation.json"
        text_path = output_dir / f"patient_{pid}_explanation.txt"

        json_path.write_text(dumps_json(report.to_dict()), encoding="utf-8")
        text_path.write_text(report.to_text(), encoding="utf-8")
        logger.info("Saved patient report -> %s", text_path)
        return json_path, text_path
