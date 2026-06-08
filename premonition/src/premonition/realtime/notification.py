"""Notification System — in-process alert notification dispatch."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone

from premonition.realtime.schemas import AlertRecord, RealtimeEvent


class NotificationSystem:
    """
    Central notification bus for realtime alerts.

    Maintains a ring buffer of recent notifications for API polling
    and pushes to streaming hub subscribers.
    """

    def __init__(self, max_buffer: int = 200) -> None:
        self._buffer: deque[dict] = deque(maxlen=max_buffer)
        self._total_sent: int = 0

    def notify_alert(self, alert: AlertRecord) -> RealtimeEvent:
        payload = alert.to_audit_dict()
        self._buffer.appendleft(payload)
        self._total_sent += 1
        return RealtimeEvent(
            event_type="alert",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=payload,
        )

    def notify_info(self, message: str, patient_id: str | None = None) -> RealtimeEvent:
        payload = {"message": message, "patient_id": patient_id}
        self._buffer.appendleft(payload)
        self._total_sent += 1
        return RealtimeEvent(
            event_type="notification",
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=payload,
        )

    def recent(self, limit: int = 50) -> list[dict]:
        return list(self._buffer)[:limit]

    @property
    def total_sent(self) -> int:
        return self._total_sent
