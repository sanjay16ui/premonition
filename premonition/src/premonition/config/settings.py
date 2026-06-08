"""Application settings loaded from environment and YAML configs."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()


def _project_root() -> Path:
    """Resolve project root (premonition/)."""
    return Path(__file__).resolve().parents[3]


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@dataclass(frozen=True)
class Settings:
    """Central configuration for PREMONITION Phase 1."""

    project_root: Path
    data_raw_dir: Path
    data_processed_dir: Path
    models_dir: Path
    reports_dir: Path
    logs_dir: Path

    dataset_filename: str = "dataset.csv"
    target_column: str = "sepsis_label"
    primary_tier: str = "t1"
    primary_model: str = "xgboost"
    random_state: int = 42
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    feature_config: dict[str, Any] = field(default_factory=dict)
    model_config: dict[str, Any] = field(default_factory=dict)

    @property
    def dataset_path(self) -> Path:
        return self.data_raw_dir / self.dataset_filename

    @property
    def feature_config_path(self) -> Path:
        return self.project_root / "src" / "premonition" / "config" / "feature_tiers.yaml"

    @property
    def model_config_path(self) -> Path:
        return self.project_root / "src" / "premonition" / "config" / "model_config.yaml"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    root = _project_root()

    feature_cfg = _load_yaml(root / "src" / "premonition" / "config" / "feature_tiers.yaml")
    model_cfg = _load_yaml(root / "src" / "premonition" / "config" / "model_config.yaml")

    return Settings(
        project_root=root,
        data_raw_dir=Path(os.getenv("PREMONITION_DATA_RAW", root / "data" / "raw")),
        data_processed_dir=Path(os.getenv("PREMONITION_DATA_PROCESSED", root / "data" / "processed")),
        models_dir=Path(os.getenv("PREMONITION_MODELS_DIR", root / "models" / "artifacts")),
        reports_dir=Path(os.getenv("PREMONITION_REPORTS_DIR", root / "reports")),
        logs_dir=Path(os.getenv("PREMONITION_LOGS_DIR", root / "logs")),
        dataset_filename=os.getenv("PREMONITION_DATASET", "dataset.csv"),
        target_column=os.getenv("PREMONITION_TARGET", model_cfg.get("target_column", "sepsis_label")),
        primary_tier=os.getenv("PREMONITION_TIER", model_cfg.get("primary_tier", "t1")),
        primary_model=os.getenv("PREMONITION_MODEL", "xgboost"),
        random_state=int(os.getenv("PREMONITION_RANDOM_STATE", "42")),
        log_level=os.getenv("PREMONITION_LOG_LEVEL", "INFO"),
        api_host=os.getenv("PREMONITION_API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("PREMONITION_API_PORT", "8000")),
        feature_config=feature_cfg,
        model_config=model_cfg,
    )
