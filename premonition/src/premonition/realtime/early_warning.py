"""Early Warning Engine — proactive clinical warnings."""

from __future__ import annotations

from premonition.realtime.schemas import (
    AlertLevel,
    AlertRecord,
    PatientMonitorState,
    VitalsSnapshot,
)


class EarlyWarningEngine:
    """
    Generate early warnings before full alert escalation.

    Detects subtle patterns that precede sepsis deterioration.
    """

    def check(
        self,
        state: PatientMonitorState,
        vitals: VitalsSnapshot,
        prev_vitals: VitalsSnapshot | None,
    ) -> list[str]:
        warnings: list[str] = []

        if state.risk_score >= 0.25 and state.deterioration_rate > 0.03:
            warnings.append(
                f"Early warning: Patient #{state.patient_id} risk trending upward "
                f"({state.risk_score * 100:.0f}%)"
            )

        if prev_vitals:
            if vitals.hr_mean > prev_vitals.hr_mean + 5:
                warnings.append(
                    f"Heart rate rising ({prev_vitals.hr_mean:.0f} -> {vitals.hr_mean:.0f} bpm)"
                )
            if vitals.temp_celsius_mean > 38.0 and prev_vitals.temp_celsius_mean <= 38.0:
                warnings.append(
                    f"Fever threshold crossed ({vitals.temp_celsius_mean:.1f}°C)"
                )
            if vitals.spo2_mean < 94 and prev_vitals.spo2_mean >= 94:
                warnings.append(
                    f"Oxygen saturation dropped below 94% ({vitals.spo2_mean:.1f}%)"
                )

        if vitals.shock_index and vitals.shock_index > 0.9:
            warnings.append(
                f"Shock index approaching critical ({vitals.shock_index:.2f})"
            )

        return warnings

    def should_pre_alert(self, state: PatientMonitorState) -> bool:
        return (
            state.alert_level in {AlertLevel.YELLOW, AlertLevel.ORANGE}
            and state.deterioration_rate > 0.02
        )
