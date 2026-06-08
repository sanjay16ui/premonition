"""Audit logging service — read and query prediction audit trails."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from premonition.api.schemas.responses import AuditLogItem, AuditLogResponse, PredictionHistoryItem, PredictionHistoryResponse
from premonition.config.settings import Settings
from premonition.models.prediction_logger import PredictionLogger
from premonition.tenant.isolation import filter_by_tenant
from premonition.utils.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Query prediction logs for history and audit endpoints."""

    def __init__(self, settings: Settings) -> None:
        self.logger = PredictionLogger(settings.logs_dir)

    def get_prediction_history(
        self,
        date: str | None = None,
        limit: int = 50,
        patient_id: str | None = None,
    ) -> PredictionHistoryResponse:
        """Return recent predictions (CEO dashboard / clinician review)."""
        records = self._fetch_records(date, limit, patient_id)
        items = [
            PredictionHistoryItem(
                timestamp=r.get("timestamp", ""),
                patient_id=r.get("patient_id", ""),
                risk_score=r.get("risk_score", 0.0),
                prediction_label=r.get("prediction_label", ""),
                confidence=r.get("confidence", ""),
                model_name=r.get("model_name", ""),
                explanation_summary=r.get("explanation_summary"),
            )
            for r in records
        ]
        return PredictionHistoryResponse(
            date=date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            count=len(items),
            items=items,
        )

    def get_audit_logs(
        self,
        date: str | None = None,
        limit: int = 100,
        prediction_label: str | None = None,
    ) -> AuditLogResponse:
        """Return full audit records with explanation details."""
        records = self._fetch_records(date, limit * 2, None)

        if prediction_label:
            records = [r for r in records if r.get("prediction_label") == prediction_label]

        records = records[:limit]
        items = [
            AuditLogItem(
                timestamp=r.get("timestamp", ""),
                patient_id=r.get("patient_id", ""),
                risk_score=r.get("risk_score", 0.0),
                prediction_label=r.get("prediction_label", ""),
                confidence=r.get("confidence", ""),
                model_name=r.get("model_name", ""),
                model_version=r.get("model_version", ""),
                explanation_summary=r.get("explanation_summary", ""),
                top_factors=r.get("top_factors", []),
                request_id=r.get("request_id"),
            )
            for r in records
        ]
        return AuditLogResponse(
            date=date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            count=len(items),
            items=items,
        )

    def _fetch_records(
        self,
        date: str | None,
        limit: int,
        patient_id: str | None,
    ) -> list[dict[str, Any]]:
        records = filter_by_tenant(self.logger.read_log(date))
        if patient_id:
            records = [r for r in records if r.get("patient_id") == str(patient_id)]
        return records[-limit:]
