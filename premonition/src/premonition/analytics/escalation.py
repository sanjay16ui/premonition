"""Smart escalation workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EscalationStep:
    level: int
    action: str
    notify: list[str]
    timeframe_minutes: int


class SmartEscalationWorkflow:
    """Define and evaluate escalation paths for deteriorating patients."""

    WORKFLOW = [
        EscalationStep(1, "Increase monitoring frequency", ["bedside_nurse"], 15),
        EscalationStep(2, "Notify charge nurse", ["charge_nurse"], 10),
        EscalationStep(3, "Physician assessment", ["attending", "hospitalist"], 15),
        EscalationStep(4, "ICU team activation", ["icu_team", "intensivist"], 10),
        EscalationStep(5, "Code sepsis protocol", ["rapid_response", "icu_team"], 5),
    ]

    def evaluate(self, risk_score: float, velocity: float, alert_level: str) -> dict[str, Any]:
        level = alert_level.upper()
        step_idx = 0
        if risk_score >= 0.75 or level == "BLACK":
            step_idx = 4
        elif risk_score >= 0.55 or level == "RED":
            step_idx = 3
        elif risk_score >= 0.35 or level == "ORANGE":
            step_idx = 2
        elif velocity > 0.15:
            step_idx = 1
        else:
            step_idx = 0

        if velocity > 0.2 and step_idx < 4:
            step_idx = min(step_idx + 1, 4)

        step = self.WORKFLOW[step_idx]
        return {
            "escalation_level": step.level,
            "action": step.action,
            "notify": step.notify,
            "timeframe_minutes": step.timeframe_minutes,
            "risk_score": risk_score,
            "velocity": velocity,
            "alert_level": level,
            "next_steps": [s.action for s in self.WORKFLOW[step_idx:step_idx + 2]],
        }
