"""Prediction endpoints."""

from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, UploadFile

from premonition.api.dependencies import (
    MetricsRecorderDep,
    PredictionSvcDep,
    RequestIdDep,
)
from premonition.api.errors import APIError
from premonition.api.schemas.requests import BatchPredictRequest, PredictRequest
from premonition.api.schemas.responses import BatchPredictResponse, PredictResponse
from premonition.api.security import verify_api_key

router = APIRouter(tags=["Predictions"], dependencies=[Depends(verify_api_key)])


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Single patient prediction",
    description="Predict sepsis risk for one patient with SHAP explanation and audit logging.",
)
async def predict_one(
    body: PredictRequest,
    service: PredictionSvcDep,
    request_id: RequestIdDep,
    recorder: MetricsRecorderDep,
) -> PredictResponse:
    try:
        result = await service.predict_one(
            patient_id=body.patient_id,
            features=body.features,
            include_shap=body.include_shap,
            include_explanation=body.include_explanation,
            request_id=request_id,
        )
        recorder.record_success(result.prediction_label)
        return result
    except RuntimeError as exc:
        recorder.record_error()
        raise APIError(str(exc), status_code=503, error="prediction_failed") from exc


@router.post(
    "/predict/batch",
    response_model=BatchPredictResponse,
    summary="Batch prediction",
    description="Predict sepsis risk for up to 100 patients in one request.",
)
async def predict_batch(
    body: BatchPredictRequest,
    service: PredictionSvcDep,
    request_id: RequestIdDep,
    recorder: MetricsRecorderDep,
) -> BatchPredictResponse:
    try:
        result = await service.predict_batch(
            patients=body.patients,
            include_shap=body.include_shap,
            include_explanation=body.include_explanation,
            request_id=request_id,
        )
        for pred in result.predictions:
            recorder.record_success(pred.prediction_label)
        return result
    except RuntimeError as exc:
        recorder.record_error()
        raise APIError(str(exc), status_code=503, error="prediction_failed") from exc


@router.post(
    "/predict/upload-csv",
    response_model=BatchPredictResponse,
    summary="CSV batch prediction",
    description="Upload a CSV file with patient features for batch prediction.",
)
async def predict_upload_csv(
    service: PredictionSvcDep,
    request_id: RequestIdDep,
    recorder: MetricsRecorderDep,
    file: UploadFile = File(..., description="CSV with patient feature columns"),
    id_column: str = Form("subject_id"),
    include_shap: bool = Form(False),
) -> BatchPredictResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise APIError("Only CSV files are accepted", error="invalid_file_type")

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise APIError(f"Failed to parse CSV: {exc}", error="csv_parse_error") from exc

    if id_column not in df.columns:
        raise APIError(
            f"ID column '{id_column}' not found in CSV",
            error="missing_id_column",
        )

    try:
        result = await service.predict_csv(
            df=df,
            id_column=id_column,
            include_shap=include_shap,
            request_id=request_id,
        )
        for pred in result.predictions:
            recorder.record_success(pred.prediction_label)
        return result
    except RuntimeError as exc:
        recorder.record_error()
        raise APIError(str(exc), status_code=503, error="prediction_failed") from exc
