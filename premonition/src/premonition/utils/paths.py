"""Filesystem path helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Create directory if missing and return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamp_slug() -> str:
    """UTC timestamp string safe for filenames."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
