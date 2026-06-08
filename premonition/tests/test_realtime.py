"""Section 8 — Real-Time Intelligence Layer tests."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone

import pytest

from premonition.api.schemas.requests import PatientFeaturesRequest
from premonition.api.schemas.responses import PredictResponse
from premonition.api.version import API_PREFIX
from premonition.config.settings import get_settings
from premonition.realtime.alert_engine import AlertEngine, risk_to_alert_level
from premonition.realtime.alert_logger import AlertAuditLogger
from premonition.realtime.config import RealtimeSettings
from premonition.realtime.early_warning import EarlyWarningEngine
from premonition.realtime.escalation import RiskEscalationEngine
from premonition.realtime.event_processor import RealtimeEventProcessor
from premonition.realtime.executive import ExecutiveCommandCenter
from premonition.realtime.notification import NotificationSystem
from premonition.realtime.priority import PriorityRankingEngine
from premonition.realtime.recommendations import RecommendationEngine
from premonition.realtime.schemas import (
    AlertLevel,
    AlertRecord,
    AlertType,
    PatientMonitorState,
    VitalsSnapshot,
)
from premonition.realtime.streaming import StreamingHub
from premonition.realtime.vitals_simulator import VitalsSimulator, compute_shock_index

EXECUTIVE_URL = f"{API_PREFIX}/realtime/executive"
PATIENTS_URL = f"{API_PREFIX}/realtime/patients"
PRIORITY_URL = f"{API_PREFIX}/realtime/priority"
ALERTS_URL = f"{API_PREFIX}/realtime/alerts"
STATUS_URL = f"{API_PREFIX}/realtime/status"
STREAM_URL = f"{API_PREFIX}/realtime/stream"


@pytest.fixture
def rt_settings():
    return RealtimeSettings(
        enabled=True,
        tick_interval_seconds=0.1,
        max_patients=5,
        deterioration_threshold=0.05,
        black_risk_threshold=0.85,
    )


@pytest.fixture
def sample_state():
    return PatientMonitorState(
        patient_id="1001",
        risk_score=0.72,
        confidence="High",
        prediction_label="sepsis_alert",
        deterioration_rate=0.10,
        alert_count=2,
    )


@pytest.fixture
def sample_vitals():
    return VitalsSnapshot(
        hr_mean=110.0,
        sbp_mean=95.0,
        dbp_mean=60.0,
        spo2_mean=91.0,
        temp_celsius_mean=38.5,
        respiratory_rate_mean=26.0,
        shock_index=1.16,
    )


@pytest.fixture
def prev_vitals():
    return VitalsSnapshot(
        hr_mean=95.0,
        sbp_mean=110.0,
        dbp_mean=68.0,
        spo2_mean=95.0,
        temp_celsius_mean=37.2,
        respiratory_rate_mean=20.0,
        shock_index=0.86,
    )


class TestAlertLevels:
    def test_green(self, rt_settings):
        assert risk_to_alert_level(0.05, 0.0, rt_settings) == AlertLevel.GREEN

    def test_yellow(self, rt_settings):
        assert risk_to_alert_level(0.20, 0.0, rt_settings) == AlertLevel.YELLOW

    def test_orange(self, rt_settings):
        assert risk_to_alert_level(0.45, 0.0, rt_settings) == AlertLevel.ORANGE

    def test_red(self, rt_settings):
        assert risk_to_alert_level(0.70, 0.0, rt_settings) == AlertLevel.RED

    def test_black(self, rt_settings):
        assert risk_to_alert_level(0.90, 0.0, rt_settings) == AlertLevel.BLACK

    def test_red_from_deterioration(self, rt_settings):
        assert risk_to_alert_level(0.50, 0.10, rt_settings) == AlertLevel.RED


class TestAlertEngine:
    def test_generates_sepsis_alert(self, sample_state, sample_vitals, prev_vitals):
        engine = AlertEngine()
        alerts = engine.evaluate(sample_state, sample_vitals, prev_vitals, 0.55)
        types = {a.alert_type for a in alerts}
        assert AlertType.POSSIBLE_SEPSIS in types

    def test_generates_shock_risk(self, sample_state, sample_vitals, prev_vitals):
        engine = AlertEngine()
        alerts = engine.evaluate(sample_state, sample_vitals, prev_vitals, 0.55)
        types = {a.alert_type for a in alerts}
        assert AlertType.SHOCK_RISK in types

    def test_generates_oxygen_failure(self, sample_state, sample_vitals, prev_vitals):
        engine = AlertEngine()
        alerts = engine.evaluate(sample_state, sample_vitals, prev_vitals, 0.55)
        types = {a.alert_type for a in alerts}
        assert AlertType.OXYGEN_FAILURE in types


class TestRiskEscalation:
    def test_tracks_deterioration(self, rt_settings):
        engine = RiskEscalationEngine(rt_settings)
        state = PatientMonitorState(patient_id="1", risk_score=0.3)
        state = engine.update(state, 0.45)
        assert state.deterioration_rate == pytest.approx(0.15, abs=0.01)

    def test_is_escalating(self, rt_settings):
        engine = RiskEscalationEngine(rt_settings)
        state = PatientMonitorState(patient_id="1", deterioration_rate=0.08)
        assert engine.is_escalating(state)


class TestEarlyWarning:
    def test_detects_warnings(self, sample_state, sample_vitals, prev_vitals):
        engine = EarlyWarningEngine()
        warnings = engine.check(sample_state, sample_vitals, prev_vitals)
        assert len(warnings) >= 1

    def test_pre_alert_threshold(self, sample_state):
        engine = EarlyWarningEngine()
        sample_state.alert_level = AlertLevel.YELLOW
        sample_state.deterioration_rate = 0.05
        assert engine.should_pre_alert(sample_state)


class TestRecommendations:
    def test_shock_recommendation(self, sample_state, sample_vitals):
        engine = RecommendationEngine()
        alert = AlertRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            patient_id="1001",
            alert_level=AlertLevel.RED,
            alert_type=AlertType.SHOCK_RISK,
            risk_score=0.72,
            confidence="High",
            reason="Shock index elevated",
        )
        recs = engine.generate(sample_state, sample_vitals, [alert])
        assert any("shock index" in r.text.lower() for r in recs)

    def test_sepsis_recommendation(self, sample_state, sample_vitals):
        engine = RecommendationEngine()
        alert = AlertRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            patient_id="1001",
            alert_level=AlertLevel.RED,
            alert_type=AlertType.POSSIBLE_SEPSIS,
            risk_score=0.85,
            confidence="High",
            reason="High sepsis risk",
        )
        recs = engine.generate(sample_state, sample_vitals, [alert])
        assert any("clinician review" in r.text.lower() for r in recs)


class TestPriorityRanking:
    def test_ranks_by_risk(self):
        engine = PriorityRankingEngine()
        patients = [
            PatientMonitorState(patient_id="1", risk_score=0.9, confidence="High", alert_count=3),
            PatientMonitorState(patient_id="2", risk_score=0.2, confidence="Low", alert_count=0),
            PatientMonitorState(patient_id="3", risk_score=0.6, confidence="Medium", alert_count=1),
        ]
        ranking = engine.rank(patients)
        assert len(ranking.critical) >= 1
        assert ranking.critical[0].patient_id == "1"

    def test_stable_patients(self):
        engine = PriorityRankingEngine()
        patients = [
            PatientMonitorState(patient_id="1", risk_score=0.05, alert_level=AlertLevel.GREEN),
            PatientMonitorState(patient_id="2", risk_score=0.08, alert_level=AlertLevel.GREEN),
        ]
        ranking = engine.rank(patients)
        assert len(ranking.stable) == 2


class TestVitalsSimulator:
    def test_tick_changes_vitals(self, settings):
        sim = VitalsSimulator(seed=42)
        patients = sim.load_patients_from_dataset(str(settings.dataset_path), 3)
        assert len(patients) >= 1
        pid = next(iter(patients))
        original_hr = patients[pid].hr_mean
        updated = sim.tick(pid, patients[pid])
        assert updated.hr_mean != original_hr or updated.spo2_mean != patients[pid].spo2_mean

    def test_shock_index(self):
        assert compute_shock_index(100, 80) == pytest.approx(1.25)


class TestAlertLogger:
    def test_log_and_read(self, tmp_path):
        logger = AlertAuditLogger(tmp_path)
        record = AlertRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            patient_id="999",
            alert_level=AlertLevel.RED,
            alert_type=AlertType.POSSIBLE_SEPSIS,
            risk_score=0.8,
            confidence="High",
            reason="Test alert",
        )
        logger.log(record)
        records = logger.read_log()
        assert len(records) == 1
        assert records[0]["patient_id"] == "999"
        assert records[0]["alert"] == AlertType.POSSIBLE_SEPSIS.value


class TestNotificationSystem:
    def test_notify_alert(self):
        ns = NotificationSystem()
        alert = AlertRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            patient_id="1",
            alert_level=AlertLevel.ORANGE,
            alert_type=AlertType.RAPID_DETERIORATION,
            risk_score=0.5,
            confidence="Medium",
            reason="Test",
        )
        event = ns.notify_alert(alert)
        assert event.event_type == "alert"
        assert ns.total_sent == 1
        assert len(ns.recent()) == 1


class TestEventProcessor:
    def test_processes_tick(self, sample_patient_features):
        processor = RealtimeEventProcessor()
        features = PatientFeaturesRequest(**sample_patient_features)
        prediction = PredictResponse(
            patient_id="37464",
            risk_score=0.85,
            risk_pct="85.0%",
            prediction=1,
            prediction_label="sepsis_alert",
            confidence="High",
            risk_category="red",
            model_name="logistic_regression",
            model_version="0.1.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        state, alerts, events = processor.process_vitals_tick(
            "37464", features, None, prediction
        )
        assert state.risk_score == 0.85
        assert any(e.event_type == "patient_update" for e in events)


class TestStreamingHub:
    def test_broadcast_sse(self, rt_settings):
        async def _run():
            hub = StreamingHub(rt_settings)
            queue = await hub.subscribe_sse()
            from premonition.realtime.schemas import RealtimeEvent

            event = RealtimeEvent(event_type="test", data={"msg": "hello"})
            await hub.broadcast(event)
            received = await asyncio.wait_for(queue.get(), timeout=2.0)
            assert received is not None
            assert received.event_type == "test"
            await hub.shutdown()

        asyncio.run(_run())

    def test_ws_subscribe_message(self, rt_settings):
        async def _run():
            hub = StreamingHub(rt_settings)

            class FakeWS:
                sent: list[str] = []

                async def send_text(self, text: str) -> None:
                    self.sent.append(text)

            ws = FakeWS()
            hub._ws_clients = [ws]  # type: ignore
            hub._ws_subscriptions[ws] = set()  # type: ignore
            await hub.handle_ws_message(ws, json.dumps({"action": "subscribe", "patient_id": "100"}))
            assert "100" in hub._ws_subscriptions[ws]
            await hub.shutdown()

        asyncio.run(_run())


class TestExecutiveCenter:
    def test_build_summary(self, tmp_path):
        logger = AlertAuditLogger(tmp_path)
        exec_center = ExecutiveCommandCenter(logger)
        patients = {
            "1": PatientMonitorState(
                patient_id="1", risk_score=0.8, alert_level=AlertLevel.RED, alert_count=2
            ),
            "2": PatientMonitorState(
                patient_id="2", risk_score=0.1, alert_level=AlertLevel.GREEN, alert_count=0
            ),
        }
        summary = exec_center.build_summary(patients, predictions_today=10, uptime_seconds=3600)
        assert summary.current_icu_patients == 2
        assert summary.high_risk_count >= 1
        assert summary.predictions_today == 10


class TestRealtimeAPI:
    def test_realtime_status(self, client):
        response = client.get(STATUS_URL)
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "patients_monitored" in data

    def test_executive_endpoint(self, client):
        response = client.get(EXECUTIVE_URL)
        assert response.status_code == 200
        data = response.json()
        assert "current_icu_patients" in data
        assert "high_risk_count" in data
        assert "average_risk_score" in data

    def test_patients_endpoint(self, client):
        response = client.get(PATIENTS_URL)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_priority_endpoint(self, client):
        response = client.get(PRIORITY_URL)
        assert response.status_code == 200
        data = response.json()
        assert "critical" in data
        assert "escalating" in data
        assert "stable" in data

    def test_alerts_endpoint(self, client):
        response = client.get(ALERTS_URL)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
