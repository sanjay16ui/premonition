"""Real-Time Event Processor — orchestrates vitals tick through all engines."""

from __future__ import annotations

from datetime import datetime, timezone

from premonition.api.schemas.requests import PatientFeaturesRequest
from premonition.api.schemas.responses import PredictResponse
from premonition.realtime.alert_engine import AlertEngine, risk_to_alert_level
from premonition.realtime.early_warning import EarlyWarningEngine
from premonition.realtime.escalation import RiskEscalationEngine
from premonition.realtime.recommendations import RecommendationEngine
from premonition.realtime.schemas import (
    AlertRecord,
    PatientMonitorState,
    RealtimeEvent,
    VitalsSnapshot,
)
from premonition.realtime.vitals_simulator import VitalsSimulator


class RealtimeEventProcessor:
    """
    Process one monitoring cycle for a patient.

    Flow: vitals update -> predict -> escalate -> alert -> recommend -> state update
    """

    def __init__(self) -> None:
        self.escalation = RiskEscalationEngine()
        self.alert_engine = AlertEngine()
        self.early_warning = EarlyWarningEngine()
        self.recommendations = RecommendationEngine()
        self.vitals_sim = VitalsSimulator()

    def process_vitals_tick(
        self,
        patient_id: str,
        features: PatientFeaturesRequest,
        state: PatientMonitorState | None,
        prediction: PredictResponse,
    ) -> tuple[PatientMonitorState, list[AlertRecord], list[RealtimeEvent]]:
        events: list[RealtimeEvent] = []
        now = datetime.now(timezone.utc).isoformat()

        prev_vitals = state.vitals if state else None
        vitals = self.vitals_sim.to_vitals_snapshot(features)

        if state is None:
            state = PatientMonitorState(patient_id=patient_id)

        prev_risk = state.risk_score
        state = self.escalation.update(state, prediction.risk_score)
        state.risk_category = prediction.risk_category
        state.confidence = prediction.confidence
        state.prediction_label = prediction.prediction_label
        state.alert_level = risk_to_alert_level(
            state.risk_score, state.deterioration_rate, self.escalation.settings
        )
        state.vitals = vitals
        state.last_updated = now

        warnings = self.early_warning.check(state, vitals, prev_vitals)
        for w in warnings:
            events.append(RealtimeEvent(event_type="early_warning", data={"message": w, "patient_id": patient_id}))

        alerts = self.alert_engine.evaluate(state, vitals, prev_vitals, prev_risk)
        state.active_alerts = alerts[-5:]
        state.alert_count += len(alerts)

        recs = self.recommendations.generate(state, vitals, alerts)
        state.recommendations = recs
        for alert in alerts:
            if recs:
                alert.recommendation = recs[0].text

        events.append(RealtimeEvent(
            event_type="patient_update",
            data={
                "patient": state.model_dump(),
                "prediction": prediction.model_dump(),
            },
        ))

        if alerts:
            events.append(RealtimeEvent(
                event_type="alerts",
                data={"patient_id": patient_id, "alerts": [a.to_audit_dict() for a in alerts]},
            ))

        return state, alerts, events
