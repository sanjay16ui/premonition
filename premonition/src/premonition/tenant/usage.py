"""Tenant usage tracking service."""

from __future__ import annotations

from premonition.tenant.models import TenantUsageRecord
from premonition.tenant.store import TenantStore


class UsageTracker:
    """Track per-tenant API and feature usage for billing and analytics."""

    METRICS = (
        "predictions", "copilot_requests", "analytics_queries",
        "realtime_events", "storage_bytes", "api_calls",
    )

    def __init__(self, store: TenantStore) -> None:
        self.store = store

    def track(self, tenant_id: str, metric: str, amount: int = 1) -> TenantUsageRecord:
        if metric not in self.METRICS:
            raise ValueError(f"Unknown metric: {metric}")
        return self.store.increment_usage(tenant_id, metric, amount)

    def get_current_usage(self, tenant_id: str) -> TenantUsageRecord:
        from datetime import datetime, timezone
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        return self.store.get_usage(tenant_id, period)

    def get_usage_history(self, tenant_id: str, limit: int = 12) -> list[TenantUsageRecord]:
        records = self.store.list_usage(tenant_id)
        return sorted(records, key=lambda r: r.period, reverse=True)[:limit]
