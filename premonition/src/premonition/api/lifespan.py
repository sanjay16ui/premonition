"""FastAPI application lifespan — startup and shutdown."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from premonition.analytics.service import AnalyticsService
from premonition.auth.email_service import ResendEmailService
from premonition.auth.otp_store import OTPStore
from premonition.copilot.service import CopilotService
from premonition.tenant.service import TenantService
from premonition.api.services.audit import AuditService
from premonition.api.services.explainability import ExplainabilityService
from premonition.api.services.metrics import MetricsCollector, MetricsService
from premonition.api.services.model_loader import ModelLoaderService
from premonition.api.services.prediction import PredictionService
from premonition.api.services.realtime import RealtimeService
from premonition.config.settings import get_settings
from premonition.realtime.config import RealtimeSettings
from premonition.realtime.monitoring import LiveMonitoringEngine
from premonition.realtime.streaming import StreamingHub
from premonition.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Startup
    -------
    1. Configure logging
    2. Load best model + preprocessor from registry
    3. Initialize all services and attach to app.state

    Shutdown
    --------
    1. Log shutdown
    2. Release resources (model references cleared)
    """
    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("PREMONITION API starting up (tier=%s)", settings.primary_tier)

    # Initialize services
    model_loader = ModelLoaderService(settings)
    await model_loader.load()

    metrics_collector = MetricsCollector()
    app.state.settings = settings
    app.state.model_loader = model_loader
    app.state.metrics_collector = metrics_collector
    app.state.prediction_service = PredictionService(model_loader)
    app.state.explainability_service = ExplainabilityService(model_loader)
    app.state.audit_service = AuditService(settings)
    app.state.metrics_service = MetricsService(model_loader, metrics_collector)
    app.state.analytics_service = AnalyticsService(settings)
    app.state.copilot_service = CopilotService(settings, app.state.analytics_service)
    app.state.tenant_service = TenantService(settings.logs_dir)

    # OTP authentication services — skip if already injected (e.g. by tests)
    if not getattr(app.state, 'otp_store', None):
        app.state.otp_store = OTPStore(settings.logs_dir)
    if not getattr(app.state, 'email_service', None):
        app.state.email_service = ResendEmailService()
    logger.info("OTP store and email service initialized (dev_mode=%s)", app.state.email_service._dev_mode)

    # Realtime intelligence layer
    rt_settings = RealtimeSettings.from_env()
    streaming_hub = StreamingHub(rt_settings)
    monitoring_engine = LiveMonitoringEngine(
        settings=settings,
        model_loader=model_loader,
        prediction_service=app.state.prediction_service,
        streaming_hub=streaming_hub,
        rt_settings=rt_settings,
    )
    app.state.streaming_hub = streaming_hub
    app.state.monitoring_engine = monitoring_engine
    app.state.realtime_service = RealtimeService(
        engine=monitoring_engine,
        hub=streaming_hub,
        alert_logger=monitoring_engine.alert_logger,
        notifications=monitoring_engine.notifications,
    )

    if model_loader.is_ready():
        logger.info("API ready — model '%s' loaded", model_loader.state.model.name)
        if rt_settings.enabled:
            monitoring_engine.initialize_patients()
            await monitoring_engine.start()
    else:
        logger.error("API started but model NOT loaded: %s", model_loader.state.load_error)

    yield

    logger.info("PREMONITION API shutting down")
    await monitoring_engine.stop()
    await streaming_hub.shutdown()
    # Close persistent HTTP connection pool for email service
    if hasattr(app.state, "email_service") and app.state.email_service:
        try:
            await app.state.email_service.close()
        except Exception:
            pass
    app.state.model_loader = None
