"""Executive Command Center Services."""

from __future__ import annotations

from premonition.realtime.alert_logger import AlertAuditLogger
from premonition.realtime.priority import PriorityRankingEngine
from premonition.realtime.schemas import AlertLevel, ExecutiveSummary, PatientMonitorState


class ExecutiveCommandCenter:
    """Aggregate realtime data for CEO / leadership dashboard."""

    def __init__(
        self,
        alert_logger: AlertAuditLogger,
        priority_engine: PriorityRankingEngine | None = None,
    ) -> None:
        self.alert_logger = alert_logger
        self.priority_engine = priority_engine or PriorityRankingEngine()

    def build_summary(
        self,
        patients: dict[str, PatientMonitorState],
        predictions_today: int,
        uptime_seconds: float,
        model_accuracy: float | None = None,
    ) -> ExecutiveSummary:
        states = list(patients.values())
        ranking = self.priority_engine.rank(states)

        high_risk = sum(1 for p in states if p.risk_score >= 0.35)
        critical = sum(1 for p in states if p.alert_level in {AlertLevel.RED, AlertLevel.BLACK})
        black = sum(1 for p in states if p.alert_level == AlertLevel.BLACK)
        avg_risk = (
            sum(p.risk_score for p in states) / len(states) if states else 0.0
        )

        return ExecutiveSummary(
            current_icu_patients=len(states),
            high_risk_count=high_risk,
            critical_alert_count=critical,
            black_alert_count=black,
            average_risk_score=round(avg_risk, 4),
            predictions_today=predictions_today,
            alerts_today=self.alert_logger.count_today(),
            model_accuracy=model_accuracy,
            system_uptime_seconds=round(uptime_seconds, 2),
            top_critical=ranking.critical,
            top_escalating=ranking.escalating,
            top_stable=ranking.stable,
        )
