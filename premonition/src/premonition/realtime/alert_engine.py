"""Alert Engine — detect clinical alert conditions."""

from __future__ import annotations

from datetime import datetime, timezone

from premonition.realtime.config import RealtimeSettings
from premonition.realtime.schemas import (
    AlertLevel,
    AlertRecord,
    AlertType,
    PatientMonitorState,
    VitalsSnapshot,
)


def risk_to_alert_level(risk_score: float, deterioration_rate: float, settings: RealtimeSettings) -> AlertLevel:
    if risk_score >= settings.black_risk_threshold:
        return AlertLevel.BLACK
    if risk_score >= 0.60 or (risk_score >= 0.45 and deterioration_rate >= settings.deterioration_threshold):
        return AlertLevel.RED
    if risk_score >= 0.35:
        return AlertLevel.ORANGE
    if risk_score >= 0.15:
        return AlertLevel.YELLOW
    return AlertLevel.GREEN


class AlertEngine:
    """Evaluate patient state and generate typed clinical alerts."""

    def __init__(self, settings: RealtimeSettings | None = None) -> None:
        self.settings = settings or RealtimeSettings.from_env()

    def evaluate(
        self,
        state: PatientMonitorState,
        vitals: VitalsSnapshot,
        prev_vitals: VitalsSnapshot | None,
        prev_risk: float | None,
    ) -> list[AlertRecord]:
        alerts: list[AlertRecord] = []
        now = datetime.now(timezone.utc).isoformat()
        level = risk_to_alert_level(state.risk_score, state.deterioration_rate, self.settings)

        if state.prediction_label == "sepsis_alert" and level.value in {"ORANGE", "RED", "BLACK"}:
            alerts.append(self._record(
                now, state, AlertType.POSSIBLE_SEPSIS, level,
                f"Sepsis probability {state.risk_score * 100:.0f}% with {state.confidence} confidence",
            ))

        if state.deterioration_rate >= self.settings.deterioration_threshold:
            alerts.append(self._record(
                now, state, AlertType.RAPID_DETERIORATION, level,
                f"Risk increased {state.deterioration_rate * 100:.1f}% since last assessment",
            ))

        if prev_vitals and vitals.spo2_mean < prev_vitals.spo2_mean - 1.0:
            if vitals.spo2_mean < 92:
                alerts.append(self._record(
                    now, state, AlertType.OXYGEN_FAILURE, level,
                    f"SpO2 decreasing to {vitals.spo2_mean:.1f}% — oxygen assessment needed",
                ))

        if vitals.shock_index and vitals.shock_index > 1.0:
            alerts.append(self._record(
                now, state, AlertType.SHOCK_RISK, level,
                f"Shock index elevated at {vitals.shock_index:.2f} (HR/SBP ratio)",
            ))

        if prev_vitals:
            if vitals.sbp_mean < prev_vitals.sbp_mean - 5 and vitals.hr_mean > prev_vitals.hr_mean + 3:
                alerts.append(self._record(
                    now, state, AlertType.CARDIOVASCULAR_INSTABILITY, level,
                    f"BP falling ({vitals.sbp_mean:.0f}) while HR rising ({vitals.hr_mean:.0f})",
                ))

            if vitals.respiratory_rate_mean > prev_vitals.respiratory_rate_mean + 2:
                alerts.append(self._record(
                    now, state, AlertType.RESPIRATORY_INSTABILITY, level,
                    f"Respiratory rate increasing to {vitals.respiratory_rate_mean:.0f}/min",
                ))

        deteriorating_signals = sum([
            prev_vitals is not None and vitals.spo2_mean < (prev_vitals.spo2_mean - 0.5),
            prev_vitals is not None and vitals.sbp_mean < (prev_vitals.sbp_mean - 3),
            vitals.temp_celsius_mean > 38.0,
            state.deterioration_rate >= self.settings.deterioration_threshold,
        ])
        if deteriorating_signals >= 3:
            alerts.append(self._record(
                now, state, AlertType.MULTI_ORGAN_FAILURE_RISK, level,
                "Multiple organ systems showing simultaneous deterioration",
            ))

        if level == AlertLevel.BLACK and not alerts:
            alerts.append(self._record(
                now, state, AlertType.POSSIBLE_SEPSIS, level,
                f"Critical risk score {state.risk_score * 100:.0f}% — immediate intervention required",
            ))

        return alerts

    def _record(
        self,
        timestamp: str,
        state: PatientMonitorState,
        alert_type: AlertType,
        level: AlertLevel,
        reason: str,
    ) -> AlertRecord:
        return AlertRecord(
            timestamp=timestamp,
            patient_id=state.patient_id,
            alert_level=level,
            alert_type=alert_type,
            risk_score=state.risk_score,
            confidence=state.confidence,
            reason=reason,
        )
