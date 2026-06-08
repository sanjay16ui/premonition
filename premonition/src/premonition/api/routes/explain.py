"""Explainability endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from premonition.api.dependencies import ExplainSvcDep, MetricsRecorderDep, RequestIdDep
from premonition.api.errors import APIError
from premonition.api.schemas.requests import ExplainRequest
from premonition.api.schemas.responses import ExplainResponse
from premonition.api.security import verify_api_key

router = APIRouter(tags=["Explainability"], dependencies=[Depends(verify_api_key)])


@router.post(
    "/explain",
    response_model=ExplainResponse,
    summary="SHAP explanation",
    description="Generate detailed SHAP-based explanation for a single patient.",
)
async def explain_patient(
    body: ExplainRequest,
    service: ExplainSvcDep,
    request_id: RequestIdDep,
    recorder: MetricsRecorderDep,
) -> ExplainResponse:
    try:
        result = await service.explain(body, request_id=request_id)
        recorder.record_success("sepsis_alert" if result.risk_score >= 0.5 else "no_alert")
        return result
    except RuntimeError as exc:
        recorder.record_error()
        raise APIError(str(exc), status_code=503, error="explain_failed") from exc
