"""Tenant-specific configuration management."""

from __future__ import annotations

from typing import Any

from premonition.tenant.store import TenantStore


DEFAULT_TENANT_CONFIG: dict[str, Any] = {
    "model_tier": "t1",
    "primary_model": "xgboost",
    "realtime_enabled": True,
    "copilot_enabled": True,
    "analytics_enabled": True,
    "dashboard_theme": "dark",
    "alert_escalation_levels": 5,
    "max_patients_monitored": 50,
    "data_retention_days": 365,
    "features": {
        "shap_explainability": True,
        "executive_dashboard": True,
        "copilot_rag": True,
        "population_analytics": True,
    },
}


class TenantConfigManager:
    """Manage per-tenant feature flags and settings."""

    def __init__(self, store: TenantStore) -> None:
        self.store = store

    def get_config(self, tenant_id: str) -> dict[str, Any]:
        tenant = self.store.get_tenant(tenant_id)
        if not tenant:
            return dict(DEFAULT_TENANT_CONFIG)
        return {**DEFAULT_TENANT_CONFIG, **tenant.config}

    def update_config(self, tenant_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        tenant = self.store.update_tenant_config(tenant_id, updates)
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")
        return {**DEFAULT_TENANT_CONFIG, **tenant.config}

    def is_feature_enabled(self, tenant_id: str, feature: str) -> bool:
        config = self.get_config(tenant_id)
        features = config.get("features", {})
        if feature in features:
            return bool(features[feature])
        return bool(config.get(feature, True))
