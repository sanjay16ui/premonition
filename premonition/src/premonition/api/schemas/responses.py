"""API response models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "premonition-api"
    version: str = "0.1.0"


class SystemStatusResponse(BaseModel):
    status: str
    model_loaded: bool
    model_name: str | None = None
    model_version: str | None = None
    tier: str
    uptime_seconds: float
    predictions_served: int
    last_prediction_at: str | None = None


class ModelVersionResponse(BaseModel):
    model_name: str
    model_version: str
    tier: str
    training_timestamp: str | None = None
    dataset_hash: str | None = None
    n_features: int = 0
    feature_set: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class ContributingFactorResponse(BaseModel):
    rank: int
    feature: str
    contribution_pct: float
    direction: str
    shap_value: float | None = None
    category: str | None = None


class ShapExplanationResponse(BaseModel):
    base_value: float
    top_factors: list[ContributingFactorResponse] = Field(default_factory=list)
    risk_increasers: list[str] = Field(default_factory=list)
    risk_decreasers: list[str] = Field(default_factory=list)
    dominant_category: str | None = None


class PredictResponse(BaseModel):
    patient_id: str
    risk_score: float = Field(..., ge=0, le=1)
    risk_pct: str
    prediction: int = Field(..., ge=0, le=1)
    prediction_label: str
    confidence: str
    risk_category: str
    model_name: str
    model_version: str
    explanation_summary: str | None = None
    top_factors: list[ContributingFactorResponse] = Field(default_factory=list)
    shap: ShapExplanationResponse | None = None
    request_id: str | None = None
    timestamp: str


class BatchPredictResponse(BaseModel):
    count: int
    predictions: list[PredictResponse]
    request_id: str | None = None


class ExplainResponse(BaseModel):
    patient_id: str
    risk_score: float
    risk_pct: str
    confidence: str
    risk_category: str
    explanation_summary: str
    top_factors: list[ContributingFactorResponse]
    shap: ShapExplanationResponse
    request_id: str | None = None


class PredictionHistoryItem(BaseModel):
    timestamp: str
    patient_id: str
    risk_score: float
    prediction_label: str
    confidence: str
    model_name: str
    explanation_summary: str | None = None


class PredictionHistoryResponse(BaseModel):
    date: str
    count: int
    items: list[PredictionHistoryItem]


class AuditLogItem(BaseModel):
    timestamp: str
    patient_id: str
    risk_score: float
    prediction_label: str
    confidence: str
    model_name: str
    model_version: str
    explanation_summary: str
    top_factors: list[str] = Field(default_factory=list)
    request_id: str | None = None


class AuditLogResponse(BaseModel):
    date: str
    count: int
    items: list[AuditLogItem]


class MetricsResponse(BaseModel):
    """JSON metrics summary (Prometheus text at /metrics?format=prometheus)."""

    predictions_total: int
    predictions_sepsis_alerts: int
    predictions_errors: int
    model_loaded: int
    uptime_seconds: float
    avg_latency_ms: float
