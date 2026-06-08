"""System status endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from premonition.api.dependencies import MetricsSvcDep, SettingsDep, get_model_loader
from premonition.api.services.model_loader import ModelLoaderService
from premonition.api.schemas.responses import SystemStatusResponse
from premonition.api.security import verify_api_key

router = APIRouter(tags=["System"], dependencies=[Depends(verify_api_key)])


@router.get(
    "/system/status",
    response_model=SystemStatusResponse,
    summary="System status",
    description="Operational status including model load state and prediction counters.",
)
async def system_status(
    model_loader: Annotated[ModelLoaderService, Depends(get_model_loader)],
    metrics: MetricsSvcDep,
    settings: SettingsDep,
) -> SystemStatusResponse:
    state = model_loader.state
    collector = metrics.collector
    status = "ready" if model_loader.is_ready() else "degraded"

    return SystemStatusResponse(
        status=status,
        model_loaded=model_loader.is_ready(),
        model_name=state.model.name if state.model else None,
        model_version=state.metadata.get("model_version"),
        tier=settings.primary_tier,
        uptime_seconds=round(collector.uptime_seconds, 2),
        predictions_served=collector.predictions_total,
        last_prediction_at=collector.last_prediction_at,
    )
