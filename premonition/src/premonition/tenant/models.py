"""Tenant domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Organization:
    id: str
    name: str
    slug: str
    contact_email: str
    region: str = "us-east-1"
    plan: str = "standard"
    status: str = "active"
    created_at: str = field(default_factory=_now_iso)


@dataclass
class Tenant:
    id: str
    hospital_name: str
    slug: str
    organization_id: str
    timezone: str = "UTC"
    bed_capacity: int = 100
    icu_beds: int = 20
    status: str = "active"
    created_at: str = field(default_factory=_now_iso)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantMember:
    email: str
    role: str
    tenant_id: str
    active: bool = True


@dataclass
class TenantUsageRecord:
    tenant_id: str
    period: str  # YYYY-MM
    predictions: int = 0
    copilot_requests: int = 0
    analytics_queries: int = 0
    realtime_events: int = 0
    storage_bytes: int = 0
    api_calls: int = 0


@dataclass
class BillingPlan:
    tenant_id: str
    plan: str = "standard"
    monthly_limit_predictions: int = 100_000
    monthly_limit_copilot: int = 10_000
    monthly_limit_api_calls: int = 500_000
    overage_allowed: bool = False
