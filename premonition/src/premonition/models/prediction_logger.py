"""Prediction logging for audit trails and CEO dashboard analytics."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir
from premonition.utils.serialization import dumps_json

logger = get_logger(__name__)


class PredictionLogger:
    """
    Append-only prediction log (JSON Lines format).

    Every prediction is saved with:
    - timestamp
    - risk score
    - prediction (0/1)
    - explanation summary
    - top contributing factors

    File format: logs/predictions/predictions_YYYY-MM-DD.jsonl
    One JSON object per line — easy to load into dashboards or databases.
    """

    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = ensure_dir(logs_dir / "predictions")

    def log(
        self,
        patient_id: int | str,
        risk_score: float,
        prediction: int,
        confidence: str,
        model_name: str,
        model_version: str,
        explanation_summary: str,
        top_factors: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> Path:
        """Append one prediction record to today's log file."""
        tenant_id = None
        try:
            from premonition.tenant.context import get_tenant_context
            tenant_id = get_tenant_context().tenant_id
        except Exception:
            pass

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "patient_id": str(patient_id),
            "risk_score": round(risk_score, 4),
            "risk_pct": f"{risk_score * 100:.1f}%",
            "prediction": prediction,
            "prediction_label": "sepsis_alert" if prediction == 1 else "no_alert",
            "confidence": confidence,
            "model_name": model_name,
            "model_version": model_version,
            "explanation_summary": explanation_summary,
            "top_factors": top_factors or [],
            **(extra or {}),
        }

        log_path = self._today_log_path()
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(dumps_json(record).replace("\n", "") + "\n")

        logger.debug("Logged prediction for patient %s -> %s", patient_id, log_path)
        return log_path

    def read_log(self, date: str | None = None) -> list[dict[str, Any]]:
        """Read all predictions for a given date (YYYY-MM-DD) or today."""
        import json

        log_path = self.logs_dir / f"predictions_{date or _today_str()}.jsonl"
        if not log_path.exists():
            return []

        records = []
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
        return records

    def _today_log_path(self) -> Path:
        return self.logs_dir / f"predictions_{_today_str()}.jsonl"


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
