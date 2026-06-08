"""Realtime event, alert, and patient state schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AlertLevel(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    ORANGE = "ORANGE"
    RED = "RED"
    BLACK = "BLACK"


class AlertType(str, Enum):
    RAPID_DETERIORATION = "Rapid Deterioration"
    POSSIBLE_SEPSIS = "Possible Sepsis"
    OXYGEN_FAILURE = "Oxygen Failure"
    SHOCK_RISK = "Shock Risk"
    CARDIOVASCULAR_INSTABILITY = "Cardiovascular Instability"
    RESPIRATORY_INSTABILITY = "Respiratory Instability"
    MULTI_ORGAN_FAILURE_RISK = "Multi-Organ Failure Risk"


ALERT_LEVEL_DESCRIPTIONS: dict[AlertLevel, str] = {
    AlertLevel.GREEN: "Normal — continue standard monitoring",
    AlertLevel.YELLOW: "Monitor closely — early warning signs detected",
    AlertLevel.ORANGE: "High risk — increased observation required",
    AlertLevel.RED: "Critical — urgent clinical review recommended",
    AlertLevel.BLACK: "Immediate intervention required",
}


class VitalsSnapshot(BaseModel):
    hr_mean: float
    sbp_mean: float
    dbp_mean: float
    spo2_mean: float
    temp_celsius_mean: float
    respiratory_rate_mean: float
    shock_index: float | None = None


class Recommendation(BaseModel):
    text: str
    reason: str
    priority: str = "medium"
    related_factors: list[str] = Field(default_factory=list)


class AlertRecord(BaseModel):
    timestamp: str
    patient_id: str
    alert_level: AlertLevel
    alert_type: AlertType
    risk_score: float
    confidence: str
    reason: str
    recommendation: str | None = None
    request_id: str | None = None

    def to_audit_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "patient_id": self.patient_id,
            "alert_level": self.alert_level.value,
            "alert_type": self.alert_type.value,
            "alert": self.alert_type.value,
            "risk": self.risk_score,
            "confidence": self.confidence,
            "reason": self.reason,
            "recommendation": self.recommendation,
            "request_id": self.request_id,
        }


class PatientMonitorState(BaseModel):
    patient_id: str
    risk_score: float = 0.0
    risk_category: str = "green"
    alert_level: AlertLevel = AlertLevel.GREEN
    confidence: str = "Low"
    prediction_label: str = "no_alert"
    deterioration_rate: float = 0.0
    alert_count: int = 0
    active_alerts: list[AlertRecord] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    vitals: VitalsSnapshot | None = None
    risk_history: list[float] = Field(default_factory=list)
    last_updated: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    priority_score: float = 0.0
    rank: int = 0


class RealtimeEvent(BaseModel):
    event_type: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    data: dict[str, Any] = Field(default_factory=dict)


class ExecutiveSummary(BaseModel):
    current_icu_patients: int
    high_risk_count: int
    critical_alert_count: int
    black_alert_count: int
    average_risk_score: float
    predictions_today: int
    alerts_today: int
    model_accuracy: float | None = None
    system_uptime_seconds: float = 0.0
    top_critical: list[PatientMonitorState] = Field(default_factory=list)
    top_escalating: list[PatientMonitorState] = Field(default_factory=list)
    top_stable: list[PatientMonitorState] = Field(default_factory=list)


class PriorityRanking(BaseModel):
    critical: list[PatientMonitorState] = Field(default_factory=list)
    escalating: list[PatientMonitorState] = Field(default_factory=list)
    stable: list[PatientMonitorState] = Field(default_factory=list)
