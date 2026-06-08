"""Backup and restore tests."""

from __future__ import annotations

import zipfile
from pathlib import Path

from premonition.ops.backup import BackupService


def test_daily_backup_creates_archive(tmp_path):
    models = tmp_path / "models"
    logs = tmp_path / "logs"
    models.mkdir()
    logs.mkdir()
    (models / "model.joblib").write_text("model-data")
    (logs / "app.log").write_text("log-data")

    svc = BackupService(tmp_path, tmp_path / "backups")
    result = svc.run_backup("daily", models, logs)
    assert result.path.exists()
    assert result.path.suffix == ".zip"
    assert "models" in result.components
    assert "logs" in result.components


def test_weekly_backup_includes_data(tmp_path):
    models = tmp_path / "models"
    logs = tmp_path / "logs"
    data = tmp_path / "data"
    for d in (models, logs, data):
        d.mkdir()
    (data / "dataset.csv").write_text("col1\n1")

    svc = BackupService(tmp_path, tmp_path / "backups")
    result = svc.run_backup("weekly", models, logs, data_dir=data)
    assert "data" in result.components

    with zipfile.ZipFile(result.path) as zf:
        names = zf.namelist()
        assert any("data" in n for n in names)


def test_backup_archive_readable(tmp_path):
    models = tmp_path / "models"
    logs = tmp_path / "logs"
    models.mkdir()
    logs.mkdir()
    (models / "metrics.json").write_text('{"pr_auc": 0.95}')

    svc = BackupService(tmp_path, tmp_path / "backups")
    result = svc.run_backup("daily", models, logs)
    assert result.size_bytes > 0
