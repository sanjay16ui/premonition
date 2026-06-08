"""Health check endpoint — no authentication required."""

from __future__ import annotations

from fastapi import APIRouter

from premonition.api.schemas.responses import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns service health. Used by load balancers and Kubernetes probes.",
)
async def health_check() -> HealthResponse:
    return HealthResponse()
