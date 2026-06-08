"""Model and dataset version tracking."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from premonition import __version__ as PACKAGE_VERSION


def dataset_version(dataset_path: Path) -> dict[str, Any]:
    """
    Create a dataset version fingerprint.

    Uses file name, size, row count hash, and last-modified time
    so we can trace which data trained which model.
    """
    if not dataset_path.exists():
        return {"path": str(dataset_path), "status": "missing"}

    content = dataset_path.read_bytes()
    file_hash = hashlib.md5(content).hexdigest()[:12]

    return {
        "filename": dataset_path.name,
        "path": str(dataset_path),
        "size_bytes": dataset_path.stat().st_size,
        "content_hash": file_hash,
        "last_modified": datetime.fromtimestamp(
            dataset_path.stat().st_mtime, tz=timezone.utc
        ).isoformat(),
    }


def build_model_version_record(
    model_name: str,
    tier: str,
    feature_names: list[str],
    metrics: dict[str, Any],
    dataset_path: Path,
    training_timestamp: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build the full version record stored alongside each model.

    Stored fields (per requirements):
    - model_version
    - training_timestamp
    - dataset_version
    - metrics
    - feature_set
    """
    return {
        "model_version": PACKAGE_VERSION,
        "package_version": PACKAGE_VERSION,
        "model_name": model_name,
        "tier": tier,
        "training_timestamp": training_timestamp or datetime.now(timezone.utc).isoformat(),
        "dataset_version": dataset_version(dataset_path),
        "metrics": metrics,
        "feature_set": feature_names,
        "n_features": len(feature_names),
        **(extra or {}),
    }
