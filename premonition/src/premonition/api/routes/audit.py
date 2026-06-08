"""Audit and prediction history endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from premonition.api.dependencies import AuditSvcDep
from premonition.api.schemas.responses import AuditLogResponse, PredictionHistoryResponse
from premonition.api.security import verify_api_key

router = APIRouter(tags=["Audit"], dependencies=[Depends(verify_api_key)])


@router.get(
    "/predictions/history",
    response_model=PredictionHistoryResponse,
    summary="Prediction history",
    description="Retrieve recent predictions for clinician review or dashboards.",
)
async def prediction_history(
    audit: AuditSvcDep,
    date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    limit: int = Query(50, ge=1, le=500),
    patient_id: str | None = Query(None),
) -> PredictionHistoryResponse:
    return audit.get_prediction_history(date=date, limit=limit, patient_id=patient_id)


@router.get(
    "/audit/logs",
    response_model=AuditLogResponse,
    summary="Audit logs",
    description="Full audit trail with explanation summaries and top factors.",
)
async def audit_logs(
    audit: AuditSvcDep,
    date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    limit: int = Query(100, ge=1, le=1000),
    prediction_label: str | None = Query(None, pattern=r"^(sepsis_alert|no_alert)$"),
) -> AuditLogResponse:
    return audit.get_audit_logs(
        date=date,
        limit=limit,
        prediction_label=prediction_label,
    )
