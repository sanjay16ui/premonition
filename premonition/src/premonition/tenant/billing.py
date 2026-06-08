"""Tenant billing abstraction — plan limits and overage checks."""

from __future__ import annotations

from premonition.tenant.models import BillingPlan, TenantUsageRecord
from premonition.tenant.store import TenantStore


class BillingService:
    """Abstract billing layer for SaaS metering."""

    PLAN_LIMITS: dict[str, dict[str, int]] = {
        "starter": {
            "monthly_limit_predictions": 10_000,
            "monthly_limit_copilot": 1_000,
            "monthly_limit_api_calls": 50_000,
        },
        "standard": {
            "monthly_limit_predictions": 100_000,
            "monthly_limit_copilot": 10_000,
            "monthly_limit_api_calls": 500_000,
        },
        "enterprise": {
            "monthly_limit_predictions": 1_000_000,
            "monthly_limit_copilot": 100_000,
            "monthly_limit_api_calls": 5_000_000,
        },
    }

    def __init__(self, store: TenantStore) -> None:
        self.store = store

    def get_plan(self, tenant_id: str) -> BillingPlan:
        plan = self.store.get_billing(tenant_id)
        if plan:
            return plan
        return BillingPlan(tenant_id=tenant_id, plan="standard")

    def check_limit(self, tenant_id: str, metric: str) -> bool:
        """Return True if tenant is within plan limits."""
        plan = self.get_plan(tenant_id)
        from datetime import datetime, timezone
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        usage = self.store.get_usage(tenant_id, period)

        limits = {
            "predictions": plan.monthly_limit_predictions,
            "copilot_requests": plan.monthly_limit_copilot,
            "api_calls": plan.monthly_limit_api_calls,
        }
        usage_map = {
            "predictions": usage.predictions,
            "copilot_requests": usage.copilot_requests,
            "api_calls": usage.api_calls,
        }
        if metric not in limits:
            return True
        if usage_map[metric] >= limits[metric]:
            return plan.overage_allowed
        return True

    def estimate_cost(self, tenant_id: str) -> dict[str, float]:
        """Estimate monthly cost based on usage (USD)."""
        plan = self.get_plan(tenant_id)
        from datetime import datetime, timezone
        period = datetime.now(timezone.utc).strftime("%Y-%m")
        usage = self.store.get_usage(tenant_id, period)

        base_rates = {"starter": 499.0, "standard": 1999.0, "enterprise": 9999.0}
        base = base_rates.get(plan.plan, 1999.0)
        overage_pred = max(0, usage.predictions - plan.monthly_limit_predictions) * 0.01
        overage_copilot = max(0, usage.copilot_requests - plan.monthly_limit_copilot) * 0.05
        overage_api = max(0, usage.api_calls - plan.monthly_limit_api_calls) * 0.001

        return {
            "base_monthly": base,
            "overage_predictions": round(overage_pred, 2),
            "overage_copilot": round(overage_copilot, 2),
            "overage_api": round(overage_api, 2),
            "estimated_total": round(base + overage_pred + overage_copilot + overage_api, 2),
        }
