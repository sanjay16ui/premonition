"""Structured logging configuration with file rotation support."""

from __future__ import annotations

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Optional

_CONFIGURED = False


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging once.

    Uses infra/logging/logging.yaml when PREMONITION_LOG_FILE is set,
    otherwise falls back to console-only logging.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_file = os.getenv("PREMONITION_LOG_FILE", "")
    config_path = _find_logging_config()

    if log_file and config_path and config_path.exists():
        _setup_from_yaml(config_path, level, log_file)
    else:
        _setup_console_only(level)

    _CONFIGURED = True


def _find_logging_config() -> Path | None:
    """Locate logging.yaml relative to project root."""
    candidates = [
        Path(__file__).resolve().parents[3] / "infra" / "logging" / "logging.yaml",
        Path("infra/logging/logging.yaml"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _setup_from_yaml(config_path: Path, level: str, log_file: str) -> None:
    """Load logging config from YAML with environment overrides."""
    import yaml

    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    # Override log level and file path from environment
    config["loggers"]["premonition"]["level"] = level.upper()
    if "file" in config.get("handlers", {}):
        config["handlers"]["file"]["filename"] = log_file
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(config)


def _setup_console_only(level: str) -> None:
    """Simple console logging fallback."""
    root = logging.getLogger()
    if root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name or "premonition")


def get_audit_logger() -> logging.Logger:
    """Return the audit logger for prediction events."""
    return logging.getLogger("premonition.audit")
