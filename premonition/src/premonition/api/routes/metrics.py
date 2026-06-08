"""Metrics endpoint — JSON and Prometheus formats."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from premonition.api.dependencies import MetricsSvcDep
from premonition.api.schemas.responses import MetricsResponse
from premonition.api.security import verify_api_key

router = APIRouter(tags=["Metrics"], dependencies=[Depends(verify_api_key)])


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Operational metrics",
    description="JSON metrics summary. Use ?format=prometheus for Prometheus text exposition.",
    responses={
        200: {
            "description": "Metrics in JSON or Prometheus format",
            "content": {
                "application/json": {},
                "text/plain": {},
            },
        }
    },
)
async def metrics(
    service: MetricsSvcDep,
    format: str | None = Query(None, alias="format"),
) -> MetricsResponse | Response:
    if format == "prometheus":
        body = service.get_prometheus_metrics()
        return Response(content=body, media_type="text/plain; version=0.0.4; charset=utf-8")
    return service.get_json_metrics()
