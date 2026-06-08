"""Alert audit trail — append-only JSONL logging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from premonition.realtime.schemas import AlertRecord
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir
from premonition.utils.serialization import dumps_json

logger = get_logger(__name__)


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class AlertAuditLogger:
    """Store every alert for compliance and executive review."""

    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = ensure_dir(logs_dir / "alerts")

    def log(self, record: AlertRecord) -> Path:
        log_path = self.logs_dir / f"alerts_{_today_str()}.jsonl"
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(dumps_json(record.to_audit_dict()).replace("\n", "") + "\n")
        logger.debug("Alert logged for patient %s: %s", record.patient_id, record.alert_type.value)
        return log_path

    def read_log(self, date: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
        log_path = self.logs_dir / f"alerts_{date or _today_str()}.jsonl"
        if not log_path.exists():
            return []
        records = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records[-limit:]

    def count_today(self) -> int:
        return len(self.read_log())
