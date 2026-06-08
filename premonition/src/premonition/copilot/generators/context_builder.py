"""Clinical context builder — assembles platform data for copilot."""

from __future__ import annotations

from typing import Any


class ClinicalContextBuilder:
    """Build rich clinical context from platform services."""

    def build_patient_context(
        self,
        patient_id: str,
        prediction_logs: list[dict],
        realtime_patient: dict | None = None,
    ) -> str:
        parts = [f"Patient ID: {patient_id}"]
        patient_logs = [l for l in prediction_logs if str(l.get("patient_id")) == str(patient_id)]
        if patient_logs:
            latest = patient_logs[-1]
            parts.append(f"Latest risk score: {latest.get('risk_score', 'N/A')}")
            parts.append(f"Prediction: {latest.get('prediction', 'N/A')}")
            factors = latest.get("top_factors", [])
            if factors:
                parts.append("Top factors: " + ", ".join(str(f) for f in factors[:5]))
        if realtime_patient:
            parts.append(f"Alert level: {realtime_patient.get('alert_level', 'N/A')}")
            parts.append(f"Current risk: {realtime_patient.get('risk_score', 'N/A')}")
            vitals = realtime_patient.get("vitals", {})
            if vitals:
                parts.append(f"Vitals: HR={vitals.get('heart_rate')}, SpO2={vitals.get('spo2')}")
        return "\n".join(parts)

    def build_executive_context(self, executive_data: dict, kpis: dict | None = None) -> str:
        parts = ["Executive Dashboard Data:"]
        if executive_data:
            for k, v in executive_data.items():
                if isinstance(v, (str, int, float)):
                    parts.append(f"  {k}: {v}")
        if kpis:
            parts.append("Hospital KPIs:")
            for k, v in kpis.items():
                if isinstance(v, (str, int, float)):
                    parts.append(f"  {k}: {v}")
        return "\n".join(parts)

    def build_alert_context(self, alert_level: str, risk_score: float, factors: list[str], message: str | None = None) -> str:
        parts = [
            f"Alert Level: {alert_level}",
            f"Risk Score: {risk_score}",
        ]
        if message:
            parts.append(f"Alert Message: {message}")
        if factors:
            parts.append("Contributing factors: " + ", ".join(factors))
        return "\n".join(parts)

    def build_prediction_context(
        self, risk_score: float, label: str | None, factors: list[str], model_name: str | None = None,
    ) -> str:
        parts = [f"Risk Score: {risk_score}"]
        if label:
            parts.append(f"Prediction Label: {label}")
        if model_name:
            parts.append(f"Model: {model_name}")
        if factors:
            parts.append("SHAP Top Factors:")
            for f in factors[:10]:
                parts.append(f"  - {f}")
        return "\n".join(parts)
