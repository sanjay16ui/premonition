"""FastAPI dependency injection."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import Depends, Request

from premonition.api.errors import ModelNotLoadedError
from premonition.api.security import verify_api_key
from premonition.api.services.audit import AuditService
from premonition.api.services.explainability import ExplainabilityService
from premonition.api.services.metrics import MetricsCollector, MetricsService
from premonition.api.services.model_loader import ModelLoaderService
from premonition.api.services.prediction import PredictionService
from premonition.api.services.analytics import AnalyticsApiService
from premonition.api.services.copilot import CopilotApiService
from premonition.api.services.realtime import RealtimeService
from premonition.api.services.tenants import TenantApiService
from premonition.config.settings import Settings, get_settings
from premonition.tenant.service import TenantService


def get_app_settings() -> Settings:
    return get_settings()


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def get_model_loader(request: Request) -> ModelLoaderService:
    loader: ModelLoaderService = request.app.state.model_loader
    return loader


def require_model(loader: Annotated[ModelLoaderService, Depends(get_model_loader)]) -> ModelLoaderService:
    if not loader.is_ready():
        raise ModelNotLoadedError(loader.state.load_error or "Model not loaded")
    return loader


def get_prediction_service(request: Request) -> PredictionService:
    return request.app.state.prediction_service


def get_explainability_service(request: Request) -> ExplainabilityService:
    return request.app.state.explainability_service


def get_audit_service(request: Request) -> AuditService:
    return request.app.state.audit_service


def get_metrics_service(request: Request) -> MetricsService:
    return request.app.state.metrics_service


def get_metrics_collector(request: Request) -> MetricsCollector:
    return request.app.state.metrics_collector


class PredictionMetricsRecorder:
    """Record prediction metrics after successful inference."""

    def __init__(self, request: Request) -> None:
        self.collector: MetricsCollector = request.app.state.metrics_collector
        self._start = time.perf_counter()

    def record_success(self, prediction_label: str) -> None:
        elapsed_ms = (time.perf_counter() - self._start) * 1000
        self.collector.record_prediction(prediction_label, elapsed_ms)

    def record_error(self) -> None:
        self.collector.record_error()


def get_metrics_recorder(request: Request) -> PredictionMetricsRecorder:
    return PredictionMetricsRecorder(request)


def get_realtime_service(request: Request) -> RealtimeService:
    return request.app.state.realtime_service


def get_analytics_service(request: Request) -> AnalyticsApiService:
    return AnalyticsApiService(request.app.state.analytics_service, request)


def get_copilot_service(request: Request) -> CopilotApiService:
    return CopilotApiService(request.app.state.copilot_service, request)


def get_tenant_service(request: Request) -> TenantService:
    return request.app.state.tenant_service


def get_tenant_api_service(request: Request) -> TenantApiService:
    return TenantApiService(request.app.state.tenant_service, request)


def get_otp_store(request: Request):  # noqa: ANN201
    """Return OTPStore from app state."""
    from premonition.auth.otp_store import OTPStore
    return request.app.state.otp_store  # type: OTPStore


def get_email_service(request: Request):  # noqa: ANN201
    """Return ResendEmailService from app state."""
    from premonition.auth.email_service import ResendEmailService
    return request.app.state.email_service  # type: ResendEmailService


# Type aliases for clean route signatures
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
ApiKeyDep = Annotated[str | None, Depends(verify_api_key)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
ModelDep = Annotated[ModelLoaderService, Depends(require_model)]
PredictionSvcDep = Annotated[PredictionService, Depends(get_prediction_service)]
ExplainSvcDep = Annotated[ExplainabilityService, Depends(get_explainability_service)]
AuditSvcDep = Annotated[AuditService, Depends(get_audit_service)]
MetricsSvcDep = Annotated[MetricsService, Depends(get_metrics_service)]
MetricsRecorderDep = Annotated[PredictionMetricsRecorder, Depends(get_metrics_recorder)]
RealtimeSvcDep = Annotated[RealtimeService, Depends(get_realtime_service)]
AnalyticsSvcDep = Annotated[AnalyticsApiService, Depends(get_analytics_service)]
CopilotSvcDep = Annotated[CopilotApiService, Depends(get_copilot_service)]
TenantSvcDep = Annotated[TenantApiService, Depends(get_tenant_api_service)]
