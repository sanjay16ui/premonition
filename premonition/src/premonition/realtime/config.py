"""Realtime layer configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RealtimeSettings:
    """Configuration for live ICU monitoring simulation."""

    enabled: bool = True
    tick_interval_seconds: float = 4.0
    max_patients: int = 12
    risk_history_size: int = 20
    deterioration_threshold: float = 0.08
    black_risk_threshold: float = 0.85
    sse_heartbeat_seconds: float = 30.0
    max_connections: int = 100

    @classmethod
    def from_env(cls) -> RealtimeSettings:
        return cls(
            enabled=os.getenv("PREMONITION_REALTIME_ENABLED", "true").lower() == "true",
            tick_interval_seconds=float(os.getenv("PREMONITION_REALTIME_TICK_SEC", "4")),
            max_patients=int(os.getenv("PREMONITION_REALTIME_MAX_PATIENTS", "12")),
            risk_history_size=int(os.getenv("PREMONITION_REALTIME_HISTORY_SIZE", "20")),
            deterioration_threshold=float(os.getenv("PREMONITION_REALTIME_DETERIORATION", "0.08")),
            black_risk_threshold=float(os.getenv("PREMONITION_REALTIME_BLACK_THRESHOLD", "0.85")),
            sse_heartbeat_seconds=float(os.getenv("PREMONITION_REALTIME_SSE_HEARTBEAT", "30")),
            max_connections=int(os.getenv("PREMONITION_REALTIME_MAX_CONNECTIONS", "100")),
        )
