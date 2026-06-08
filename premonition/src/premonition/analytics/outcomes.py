"""Outcome prediction framework."""

from __future__ import annotations

from typing import Any

from premonition.analytics.schemas import OutcomePrediction, OutcomePredictionRequest


class OutcomePredictionFramework:
    """Forecast clinical outcomes based on risk and vitals."""

    OUTCOMES = {
        24: ["sepsis_onset", "icu_transfer", "vasopressor_need"],
        48: ["sepsis_onset", "organ_dysfunction", "prolonged_stay"],
        72: ["mortality_risk", "discharge_readiness", "readmission_risk"],
    }

    def predict(
        self,
        request: OutcomePredictionRequest,
        risk_score: float,
        features: dict[str, Any] | None = None,
    ) -> list[OutcomePrediction]:
        horizon = request.horizon_hours
        outcomes = self.OUTCOMES.get(horizon, self.OUTCOMES[24])
        features = features or request.patient_features or {}
        predictions: list[OutcomePrediction] = []

        hr = float(features.get("hr_mean", 80))
        spo2 = float(features.get("spo2_mean", 97))
        comorbidity = float(features.get("comorbidity_count", 0))

        for outcome in outcomes:
            prob = self._outcome_probability(outcome, risk_score, hr, spo2, comorbidity, horizon)
            factors = self._contributing_factors(outcome, features, risk_score)
            predictions.append(OutcomePrediction(
                outcome=outcome,
                probability=round(prob, 4),
                horizon_hours=horizon,
                contributing_factors=factors,
            ))
        return sorted(predictions, key=lambda p: p.probability, reverse=True)

    def _outcome_probability(
        self, outcome: str, risk: float, hr: float, spo2: float, comorbidity: float, horizon: int,
    ) -> float:
        base = risk
        horizon_factor = min(horizon / 72, 1.0)
        modifiers = {
            "sepsis_onset": base * 1.2 + (0.1 if hr > 100 else 0),
            "icu_transfer": base * 0.9 + comorbidity * 0.05,
            "vasopressor_need": base * 0.7 + (0.15 if spo2 < 92 else 0),
            "organ_dysfunction": base * 0.85 + comorbidity * 0.08,
            "prolonged_stay": base * 0.6 + comorbidity * 0.1,
            "mortality_risk": base * 0.5 + comorbidity * 0.12,
            "discharge_readiness": max(0, 1 - base - comorbidity * 0.05),
            "readmission_risk": base * 0.4 + comorbidity * 0.15,
        }
        prob = modifiers.get(outcome, base) * horizon_factor
        return min(max(prob, 0.0), 1.0)

    def _contributing_factors(self, outcome: str, features: dict[str, Any], risk: float) -> list[str]:
        factors = [f"ml_risk_score={risk:.2f}"]
        if features.get("hr_mean", 0) > 100:
            factors.append("elevated_heart_rate")
        if features.get("spo2_mean", 100) < 92:
            factors.append("hypoxemia")
        if features.get("comorbidity_count", 0) >= 3:
            factors.append("high_comorbidity_burden")
        if outcome == "mortality_risk" and risk > 0.5:
            factors.append("critical_sepsis_risk")
        return factors[:5]
