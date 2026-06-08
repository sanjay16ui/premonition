"""Live Monitoring Engine — background ICU simulation orchestrator."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from premonition.api.schemas.requests import PatientFeaturesRequest
from premonition.api.services.model_loader import ModelLoaderService
from premonition.api.services.prediction import PredictionService
from premonition.config.settings import Settings
from premonition.realtime.alert_logger import AlertAuditLogger
from premonition.realtime.config import RealtimeSettings
from premonition.realtime.event_processor import RealtimeEventProcessor
from premonition.realtime.executive import ExecutiveCommandCenter
from premonition.realtime.notification import NotificationSystem
from premonition.realtime.priority import PriorityRankingEngine
from premonition.realtime.schemas import ExecutiveSummary, PatientMonitorState, RealtimeEvent
from premonition.realtime.streaming import StreamingHub
from premonition.realtime.vitals_simulator import VitalsSimulator
from premonition.intelligence.memory.store import AgentMemoryStore
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


class LiveMonitoringEngine:
    """
    Core realtime orchestrator.

    Runs a background loop that:
    1. Updates simulated vitals
    2. Recalculates ML risk
    3. Generates alerts and recommendations
    4. Broadcasts to SSE/WebSocket clients
    """

    def __init__(
        self,
        settings: Settings,
        model_loader: ModelLoaderService,
        prediction_service: PredictionService,
        streaming_hub: StreamingHub,
        rt_settings: RealtimeSettings | None = None,
    ) -> None:
        self.settings = settings
        self.model_loader = model_loader
        self.prediction_service = prediction_service
        self.hub = streaming_hub
        self.rt_settings = rt_settings or RealtimeSettings.from_env()

        self.vitals_sim = VitalsSimulator()
        self.processor = RealtimeEventProcessor()
        self.alert_logger = AlertAuditLogger(settings.logs_dir)
        self.notifications = NotificationSystem()
        self.priority_engine = PriorityRankingEngine()
        self.executive = ExecutiveCommandCenter(self.alert_logger, self.priority_engine)
        self.memory_store = AgentMemoryStore(settings.logs_dir / "agent_memory.db")

        self._patients: dict[str, PatientFeaturesRequest] = {}
        self._states: dict[str, PatientMonitorState] = {}
        self._prev_vitals: dict[str, Any] = {}
        self._task: asyncio.Task | None = None
        self._running = False
        self._predictions_today = 0
        self._started_at = datetime.now(timezone.utc)

        # Agentic AI
        from premonition.intelligence.agents import (
            MonitoringAgent, PredictionAgent, ClinicalAgent, EscalationAgent, ExecutiveAgent, NotificationAgent, MemoryAgent
        )
        self.monitoring_agent = MonitoringAgent()
        self.prediction_agent = PredictionAgent()
        self.clinical_agent = ClinicalAgent()
        self.escalation_agent = EscalationAgent()
        self.executive_agent = ExecutiveAgent()
        self.notification_agent = NotificationAgent()
        self.memory_agent = MemoryAgent()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def patients(self) -> dict[str, PatientMonitorState]:
        return dict(self._states)

    def initialize_patients(self) -> int:
        self._patients = self.vitals_sim.load_patients_from_dataset(
            str(self.settings.dataset_path),
            self.rt_settings.max_patients,
        )
        for pid in self._patients:
            self._states[pid] = PatientMonitorState(patient_id=pid)
        logger.info("Realtime monitoring initialized with %d patients", len(self._patients))
        return len(self._patients)

    async def start(self) -> None:
        if not self.rt_settings.enabled:
            logger.info("Realtime monitoring disabled")
            return
        if self._running:
            return
        if not self._patients:
            self.initialize_patients()
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("Live monitoring engine started (tick=%ss)", self.rt_settings.tick_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Live monitoring engine stopped")

    async def _monitoring_loop(self) -> None:
        while self._running:
            try:
                await self._tick_all()
            except Exception as exc:
                logger.error("Monitoring tick error: %s", exc)
            await asyncio.sleep(self.rt_settings.tick_interval_seconds)

    async def _tick_all(self) -> None:
        for pid, features in list(self._patients.items()):
            await self._tick_patient(pid, features)

        summary = self.get_executive_summary()
        
        # Executive Agent Cycle
        icu_capacity = self.rt_settings.max_patients
        active_count = len([s for s in self._states.values() if s.alert_level in ["RED", "BLACK"]])
        exec_ctx = {"hospital_metrics": {"icu_occupancy": active_count / max(1, icu_capacity)}}
        exec_action = await self.executive_agent.run_cycle(exec_ctx)
        if exec_action.get("event"):
            self.memory_store.record_decision(
                "system", 
                self.executive_agent.name, 
                exec_action.get("explanation", {}).get("action", "Act"),
                exec_action.get("explanation", {}).get("reason", "Unknown"),
                exec_action.get("explanation", {}).get("confidence", 0.0)
            )
            await self.hub.broadcast(RealtimeEvent(
                event_type="agent_action",
                data={"patient_id": "system", **exec_action}
            ))

        await self.hub.broadcast(RealtimeEvent(
            event_type="executive_summary",
            data=summary.model_dump(),
        ))

    async def _tick_patient(self, patient_id: str, features: PatientFeaturesRequest) -> None:
        updated = self.vitals_sim.tick(patient_id, features)
        self._patients[patient_id] = updated

        try:
            prediction = await self.prediction_service.predict_one(
                patient_id=patient_id,
                features=updated,
                include_shap=False,
                include_explanation=True,
            )
        except Exception as exc:
            logger.warning("Prediction failed for %s: %s", patient_id, exc)
            return

        self._predictions_today += 1
        state = self._states.get(patient_id)
        state, alerts, events = self.processor.process_vitals_tick(
            patient_id, updated, state, prediction
        )
        self._states[patient_id] = state

        for event in events:
            await self.hub.broadcast(event)

        for alert in alerts:
            self.alert_logger.log(alert)
            notif_event = self.notifications.notify_alert(alert)
            await self.hub.broadcast(notif_event)

        # Agentic AI Cycle per patient
        agent_context = {
            "patient_id": patient_id,
            "vitals": updated.model_dump(),
            "risk_score": prediction.risk_score,
            "shap_values": prediction.top_factors,
            "unresolved_minutes": state.alert_count * 5  # simplified approximation
        }
        
        agent_context['pending_alerts'] = alerts
        agent_context['agent_decisions'] = []
        
        for agent in [self.monitoring_agent, self.prediction_agent, self.clinical_agent, self.escalation_agent, self.notification_agent, self.memory_agent]:
            action_res = await agent.run_cycle(agent_context)
            if action_res.get("event"):
                self.memory_store.record_decision(
                    patient_id,
                    agent.name,
                    action_res.get("explanation", {}).get("action", "Act"),
                    action_res.get("explanation", {}).get("reason", "Unknown"),
                    action_res.get("explanation", {}).get("confidence", 0.0)
                )
                await self.hub.broadcast(RealtimeEvent(
                    event_type="agent_action",
                    data={"patient_id": patient_id, **action_res}
                ))

    def get_executive_summary(self) -> ExecutiveSummary:
        uptime = (datetime.now(timezone.utc) - self._started_at).total_seconds()
        model_accuracy = None
        if self.model_loader.state.metadata:
            test_metrics = self.model_loader.state.metadata.get("metrics", {})
            if isinstance(test_metrics, dict):
                test = test_metrics.get("test", test_metrics)
                if isinstance(test, dict):
                    model_accuracy = test.get("pr_auc")
        return self.executive.build_summary(
            self._states,
            self._predictions_today,
            uptime,
            model_accuracy,
        )

    def get_priority_ranking(self):
        return self.priority_engine.rank(list(self._states.values()))

    def acknowledge_patient(self, patient_id: str) -> None:
        from premonition.realtime.schemas import AlertLevel
        state = self._states.get(patient_id)
        if state:
            state.alert_level = AlertLevel.GREEN
            state.active_alerts = []
            state.alert_count = 0
            state.risk_category = "green"

    def get_patient_state(self, patient_id: str) -> PatientMonitorState | None:
        return self._states.get(patient_id)
