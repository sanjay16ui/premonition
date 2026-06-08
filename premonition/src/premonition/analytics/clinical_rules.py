"""Clinical rule engine — sepsis screening criteria."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ClinicalRule:
    name: str
    description: str
    severity: str
    triggered: bool
    evidence: str


class ClinicalRuleEngine:
    """
    Apply clinical screening rules alongside ML predictions.

    Based on Sepsis-3 criteria proxies and ICU early-warning patterns.
    """

    def evaluate(self, features: dict[str, Any], risk_score: float) -> list[ClinicalRule]:
        rules: list[ClinicalRule] = []

        temp = float(features.get("temp_celsius_mean", 37))
        hr = float(features.get("hr_mean", 80))
        rr = float(features.get("respiratory_rate_mean", 16))
        spo2 = float(features.get("spo2_mean", 97))
        map_val = float(features.get("map_mean", 85))
        wbc_proxy = float(features.get("shock_index", 0.8))

        if temp > 38.3 or temp < 36.0:
            rules.append(ClinicalRule(
                "temperature_abnormal", "Abnormal temperature", "warning", True,
                f"Temp {temp:.1f}C outside 36-38.3C",
            ))
        if hr > 90:
            rules.append(ClinicalRule(
                "tachycardia", "Heart rate elevation", "warning", True, f"HR {hr:.0f} bpm > 90",
            ))
        if rr > 22:
            rules.append(ClinicalRule(
                "tachypnea", "Respiratory rate elevation", "warning", True, f"RR {rr:.0f}/min > 22",
            ))
        if spo2 < 92:
            rules.append(ClinicalRule(
                "hypoxemia", "Low oxygen saturation", "critical", True, f"SpO2 {spo2:.0f}% < 92%",
            ))
        if map_val < 65:
            rules.append(ClinicalRule(
                "hypotension", "Mean arterial pressure low", "critical", True, f"MAP {map_val:.0f} < 65",
            ))
        if wbc_proxy > 1.0:
            rules.append(ClinicalRule(
                "shock_index_elevated", "Elevated shock index", "warning", True, f"Shock index {wbc_proxy:.2f}",
            ))
        if risk_score >= 0.5:
            rules.append(ClinicalRule(
                "ml_high_risk", "ML model high sepsis risk", "critical", True,
                f"Risk score {risk_score:.2f} >= 0.50",
            ))
        elif risk_score >= 0.35:
            rules.append(ClinicalRule(
                "ml_elevated_risk", "ML model elevated risk", "warning", True,
                f"Risk score {risk_score:.2f} >= 0.35",
            ))

        return rules

    def triggered_names(self, features: dict[str, Any], risk_score: float) -> list[str]:
        return [r.name for r in self.evaluate(features, risk_score) if r.triggered]

    def clinical_score(self, features: dict[str, Any], risk_score: float) -> float:
        rules = self.evaluate(features, risk_score)
        weights = {"critical": 0.3, "warning": 0.15, "info": 0.05}
        score = sum(weights.get(r.severity, 0.1) for r in rules if r.triggered)
        return min(round(score + risk_score * 0.5, 4), 1.0)
