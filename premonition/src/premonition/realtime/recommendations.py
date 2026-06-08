"""AI Recommendation Engine — explainable clinical recommendations."""

from __future__ import annotations

from premonition.realtime.schemas import (
    AlertLevel,
    AlertRecord,
    AlertType,
    PatientMonitorState,
    Recommendation,
    VitalsSnapshot,
)


class RecommendationEngine:
    """Generate explainable, actionable clinical recommendations."""

    def generate(
        self,
        state: PatientMonitorState,
        vitals: VitalsSnapshot,
        alerts: list[AlertRecord],
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []

        for alert in alerts:
            rec = self._from_alert(alert, vitals, state)
            if rec:
                recs.append(rec)

        if not recs:
            recs.extend(self._from_state(state, vitals))

        # Deduplicate by text
        seen: set[str] = set()
        unique: list[Recommendation] = []
        for r in recs:
            if r.text not in seen:
                seen.add(r.text)
                unique.append(r)
        return unique[:5]

    def _from_alert(
        self,
        alert: AlertRecord,
        vitals: VitalsSnapshot,
        state: PatientMonitorState,
    ) -> Recommendation | None:
        mapping: dict[AlertType, tuple[str, str, str]] = {
            AlertType.SHOCK_RISK: (
                "Patient showing rising shock index. Monitor blood pressure every 15 minutes.",
                f"Shock index at {vitals.shock_index:.2f} indicates hemodynamic stress",
                "high",
            ),
            AlertType.OXYGEN_FAILURE: (
                "SpO2 decreasing continuously. Consider immediate oxygen assessment.",
                f"Oxygen saturation at {vitals.spo2_mean:.1f}% and trending down",
                "high",
            ),
            AlertType.POSSIBLE_SEPSIS: (
                "High confidence sepsis risk. Urgent clinician review recommended.",
                f"Model confidence: {state.confidence}, risk: {state.risk_score * 100:.0f}%",
                "critical" if state.alert_level == AlertLevel.BLACK else "high",
            ),
            AlertType.RAPID_DETERIORATION: (
                "Patient deteriorating rapidly. Increase monitoring frequency to every 5 minutes.",
                f"Risk increased {state.deterioration_rate * 100:.1f}% in last cycle",
                "high",
            ),
            AlertType.CARDIOVASCULAR_INSTABILITY: (
                "Cardiovascular instability detected. Check MAP and consider fluid assessment.",
                f"HR {vitals.hr_mean:.0f} bpm, SBP {vitals.sbp_mean:.0f} mmHg",
                "high",
            ),
            AlertType.RESPIRATORY_INSTABILITY: (
                "Respiratory rate increasing. Assess airway and ventilation status.",
                f"RR at {vitals.respiratory_rate_mean:.0f}/min",
                "medium",
            ),
            AlertType.MULTI_ORGAN_FAILURE_RISK: (
                "Multiple systems deteriorating. Activate rapid response team.",
                "Concurrent vitals deterioration across cardiovascular, respiratory, and metabolic systems",
                "critical",
            ),
        }
        if alert.alert_type in mapping:
            text, reason, priority = mapping[alert.alert_type]
            return Recommendation(
                text=text,
                reason=reason,
                priority=priority,
                related_factors=[alert.alert_type.value],
            )
        return None

    def _from_state(
        self,
        state: PatientMonitorState,
        vitals: VitalsSnapshot,
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []
        if state.alert_level == AlertLevel.GREEN:
            recs.append(Recommendation(
                text="Patient stable. Continue standard ICU monitoring protocol.",
                reason=f"Risk score {state.risk_score * 100:.0f}% within normal range",
                priority="low",
            ))
        elif state.alert_level == AlertLevel.YELLOW:
            recs.append(Recommendation(
                text="Elevated risk detected. Review vitals within 30 minutes.",
                reason=f"Risk at {state.risk_score * 100:.0f}% — early warning zone",
                priority="medium",
            ))
        if vitals.temp_celsius_mean > 38.3:
            recs.append(Recommendation(
                text="Elevated temperature detected. Consider infection workup.",
                reason=f"Temperature {vitals.temp_celsius_mean:.1f}°C",
                priority="medium",
                related_factors=["Temperature"],
            ))
        return recs
