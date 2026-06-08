"""Backup automation — daily, weekly, model artifacts."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from premonition.utils.logging import get_logger
from premonition.utils.paths import ensure_dir

logger = get_logger(__name__)

BackupSchedule = Literal["daily", "weekly"]


@dataclass
class BackupResult:
    schedule: BackupSchedule
    path: Path
    size_bytes: int
    timestamp: str
    components: list[str]


class BackupService:
    """Create compressed archives of models, logs, and database exports."""

    def __init__(self, project_root: Path, backup_dir: Path) -> None:
        self.project_root = project_root
        self.backup_dir = ensure_dir(backup_dir)

    def run_backup(
        self,
        schedule: BackupSchedule,
        models_dir: Path,
        logs_dir: Path,
        data_dir: Path | None = None,
    ) -> BackupResult:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        name = f"premonition_{schedule}_{ts}"
        dest = self.backup_dir / name
        ensure_dir(dest)
        components: list[str] = []

        if models_dir.exists():
            shutil.copytree(models_dir, dest / "models", dirs_exist_ok=True)
            components.append("models")

        if logs_dir.exists():
            shutil.copytree(logs_dir, dest / "logs", dirs_exist_ok=True)
            components.append("logs")

        if schedule == "weekly" and data_dir and data_dir.exists():
            shutil.copytree(data_dir, dest / "data", dirs_exist_ok=True)
            components.append("data")

        archive = shutil.make_archive(str(self.backup_dir / name), "zip", dest)
        shutil.rmtree(dest)
        archive_path = Path(archive)
        size = archive_path.stat().st_size
        logger.info("Backup %s created: %s (%d bytes)", schedule, archive_path, size)
        return BackupResult(
            schedule=schedule,
            path=archive_path,
            size_bytes=size,
            timestamp=datetime.now(timezone.utc).isoformat(),
            components=components,
        )
