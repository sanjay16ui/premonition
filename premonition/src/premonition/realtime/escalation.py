"""Risk Escalation Engine — track deterioration velocity."""

from __future__ import annotations

from premonition.realtime.config import RealtimeSettings
from premonition.realtime.schemas import AlertLevel, PatientMonitorState


class RiskEscalationEngine:
    """Compute deterioration rate and escalation status."""

    def __init__(self, settings: RealtimeSettings | None = None) -> None:
        self.settings = settings or RealtimeSettings.from_env()

    def update(self, state: PatientMonitorState, new_risk: float) -> PatientMonitorState:
        history = list(state.risk_history)
        if not history and state.risk_score > 0:
            history.append(state.risk_score)
        history.append(new_risk)
        if len(history) > self.settings.risk_history_size:
            history = history[-self.settings.risk_history_size :]

        deterioration = 0.0
        if len(history) >= 2:
            deterioration = max(0.0, history[-1] - history[-2])

        state.risk_history = history
        state.risk_score = new_risk
        state.deterioration_rate = round(deterioration, 4)
        return state

    def is_escalating(self, state: PatientMonitorState) -> bool:
        return state.deterioration_rate >= self.settings.deterioration_threshold

    def escalation_level(self, state: PatientMonitorState) -> AlertLevel:
        if state.risk_score >= self.settings.black_risk_threshold:
            return AlertLevel.BLACK
        if self.is_escalating() and state.risk_score >= 0.35:
            return AlertLevel.RED
        if self.is_escalating():
            return AlertLevel.ORANGE
        if state.risk_score >= 0.60:
            return AlertLevel.RED
        if state.risk_score >= 0.35:
            return AlertLevel.ORANGE
        if state.risk_score >= 0.15:
            return AlertLevel.YELLOW
        return AlertLevel.GREEN
