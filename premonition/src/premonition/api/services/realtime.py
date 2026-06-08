"""API service wrapper for realtime intelligence layer."""

from __future__ import annotations

from premonition.realtime.alert_logger import AlertAuditLogger
from premonition.realtime.monitoring import LiveMonitoringEngine
from premonition.realtime.notification import NotificationSystem
from premonition.realtime.schemas import ExecutiveSummary, PatientMonitorState, PriorityRanking
from premonition.realtime.streaming import StreamingHub


class RealtimeService:
    """Thin facade over LiveMonitoringEngine for API routes."""

    def __init__(
        self,
        engine: LiveMonitoringEngine,
        hub: StreamingHub,
        alert_logger: AlertAuditLogger,
        notifications: NotificationSystem,
    ) -> None:
        self.engine = engine
        self.hub = hub
        self.alert_logger = alert_logger
        self.notifications = notifications

    def get_executive_summary(self) -> ExecutiveSummary:
        return self.engine.get_executive_summary()

    def get_patients(self) -> list[PatientMonitorState]:
        return list(self.engine.patients.values())

    def get_patient(self, patient_id: str) -> PatientMonitorState | None:
        return self.engine.get_patient_state(patient_id)

    def get_priority_ranking(self) -> PriorityRanking:
        return self.engine.get_priority_ranking()

    def get_alert_history(self, limit: int = 100) -> list[dict]:
        return self.alert_logger.read_log(limit=limit)

    def get_notifications(self, limit: int = 50) -> list[dict]:
        return self.notifications.recent(limit)

    @property
    def is_running(self) -> bool:
        return self.engine.is_running

    @property
    def connection_count(self) -> int:
        return self.hub.connection_count
