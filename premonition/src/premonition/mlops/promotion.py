"""Model promotion workflow — staging, production, approval, rollback."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from premonition.utils.serialization import dumps_json
from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir

logger = get_logger(__name__)


@dataclass
class PromotionRecord:
    tier: str
    version: str
    stage: str
    approved_by: str
    timestamp: str
    action: str
    metrics: dict[str, Any]


class ModelPromotionService:
    """Staging and production model registry with approval workflow."""

    def __init__(self, models_dir: Path) -> None:
        self.models_dir = Path(models_dir)
        self.staging_dir = ensure_dir(self.models_dir / "staging")
        self.production_dir = ensure_dir(self.models_dir / "production")
        self.history_file = ensure_dir(self.models_dir) / "promotion_history.json"
        self._ensure_history()

    def _ensure_history(self) -> None:
        if not self.history_file.exists():
            self.history_file.write_text("[]", encoding="utf-8")

    def _load_history(self) -> list[dict[str, Any]]:
        return json.loads(self.history_file.read_text(encoding="utf-8"))

    def _append_history(self, record: PromotionRecord) -> None:
        history = self._load_history()
        history.append({
            "tier": record.tier,
            "version": record.version,
            "stage": record.stage,
            "approved_by": record.approved_by,
            "timestamp": record.timestamp,
            "action": record.action,
            "metrics": record.metrics,
        })
        self.history_file.write_text(dumps_json(history), encoding="utf-8")

    def _source_bundle(self, tier: str) -> Path:
        return self.models_dir / tier / "best_model"

    def promote_to_staging(self, tier: str, approved_by: str) -> dict[str, Any]:
        source = self._source_bundle(tier)
        if not source.exists():
            raise FileNotFoundError(f"No trained model for tier {tier}")
        dest = self.staging_dir / tier
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(source, dest)
        version = self._read_version(dest)
        record = PromotionRecord(
            tier=tier, version=version, stage="staging",
            approved_by=approved_by,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="promote_staging", metrics=self._read_metrics(dest),
        )
        self._append_history(record)
        logger.info("Promoted %s to staging (v%s)", tier, version)
        return {"tier": tier, "stage": "staging", "version": version}

    def approve_for_production(self, tier: str, approved_by: str) -> dict[str, Any]:
        staging = self.staging_dir / tier
        if not staging.exists():
            raise FileNotFoundError(f"No staging model for tier {tier}")
        dest = self.production_dir / tier
        backup = None
        if dest.exists():
            backup = self.production_dir / f"{tier}_backup"
            if backup.exists():
                shutil.rmtree(backup)
            shutil.copytree(dest, backup)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(staging, dest)
        version = self._read_version(dest)
        record = PromotionRecord(
            tier=tier, version=version, stage="production",
            approved_by=approved_by,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="approve_production", metrics=self._read_metrics(dest),
        )
        self._append_history(record)
        return {"tier": tier, "stage": "production", "version": version, "backup": str(backup) if backup else None}

    def rollback_production(self, tier: str, approved_by: str) -> dict[str, Any]:
        backup = self.production_dir / f"{tier}_backup"
        dest = self.production_dir / tier
        if not backup.exists():
            raise FileNotFoundError(f"No production backup for tier {tier}")
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(backup, dest)
        version = self._read_version(dest)
        record = PromotionRecord(
            tier=tier, version=version, stage="production",
            approved_by=approved_by,
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="rollback", metrics=self._read_metrics(dest),
        )
        self._append_history(record)
        return {"tier": tier, "stage": "production", "version": version, "action": "rollback"}

    def get_promotion_history(self) -> list[dict[str, Any]]:
        return self._load_history()

    def get_stage_status(self, tier: str) -> dict[str, Any]:
        return {
            "staging": self._stage_info(self.staging_dir / tier),
            "production": self._stage_info(self.production_dir / tier),
            "development": self._stage_info(self._source_bundle(tier)),
        }

    def _stage_info(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        return {
            "version": self._read_version(path),
            "metrics": self._read_metrics(path),
            "path": str(path),
        }

    def _read_version(self, bundle: Path) -> str:
        vf = bundle / "version.json"
        if vf.exists():
            return json.loads(vf.read_text(encoding="utf-8")).get("model_version", "unknown")
        return "unknown"

    def _read_metrics(self, bundle: Path) -> dict[str, Any]:
        mf = bundle / "metrics.json"
        if mf.exists():
            return json.loads(mf.read_text(encoding="utf-8"))
        return {}
