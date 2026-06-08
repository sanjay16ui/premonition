"""Analytics request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ModelScore(BaseModel):
    model_name: str
    score: float
    weight: float
    prediction: int


class EnsembleResult(BaseModel):
    ensemble_score: float
    ensemble_prediction: int
    method: str
    models_used: list[ModelScore]
    confidence: str


class ModelBenchmark(BaseModel):
    model_name: str
    pr_auc: float
    roc_auc: float
    f1: float
    precision: float
    recall: float
    brier_score: float
    rank: int = 0


class ModelComparisonResult(BaseModel):
    primary_metric: str
    winner: str
    models: list[ModelBenchmark]
    recommendation: str


class ExplainabilityComparison(BaseModel):
    model_name: str
    top_features: list[dict[str, Any]]
    category_impact: dict[str, float]


class RiskStratificationRequest(BaseModel):
    patient_ids: list[str] | None = None
    thresholds: dict[str, float] | None = None


class RiskTier(BaseModel):
    tier: str
    count: int
    percentage: float
    score_range: str


class RiskStratificationResult(BaseModel):
    tiers: list[RiskTier]
    total_patients: int
    distribution: dict[str, float]


class CohortAnalysisRequest(BaseModel):
    segment_by: str = "age_group"
    filters: dict[str, Any] = Field(default_factory=dict)


class CohortSegment(BaseModel):
    name: str
    size: int
    sepsis_rate: float
    avg_risk_score: float
    mortality_proxy: float
    top_risk_factors: list[str]


class OutcomePredictionRequest(BaseModel):
    horizon_hours: int = 24
    patient_features: dict[str, Any] | None = None


class OutcomePrediction(BaseModel):
    outcome: str
    probability: float
    horizon_hours: int
    contributing_factors: list[str]


class RecommendationRequest(BaseModel):
    patient_id: str | None = None
    risk_score: float | None = None
    top_factors: list[str] = Field(default_factory=list)


class ClinicalRecommendation(BaseModel):
    rank: int
    action: str
    priority: str
    rationale: str
    evidence_level: str


class SimulateRequest(BaseModel):
    scenario: str = "icu_surge"
    parameters: dict[str, Any] = Field(default_factory=dict)


class ExecutiveAnalytics(BaseModel):
    kpis: dict[str, Any]
    alerts_summary: dict[str, Any]
    risk_overview: dict[str, Any]
    model_performance: dict[str, Any]
    operational_status: dict[str, Any]


class PopulationAnalytics(BaseModel):
    total_patients: int
    sepsis_incidence: float
    risk_distribution: dict[str, int]
    demographic_breakdown: dict[str, Any]
    trend: list[dict[str, Any]]


class CapacityAnalytics(BaseModel):
    current_occupancy: float
    predicted_occupancy_24h: float
    predicted_occupancy_72h: float
    bed_demand_forecast: list[dict[str, Any]]
    surge_probability: float


class ResourceAnalytics(BaseModel):
    staff_utilization: float
    ventilator_utilization: float
    lab_capacity: float
    bottleneck_resources: list[str]
    forecast: list[dict[str, Any]]


class HospitalKPIs(BaseModel):
    sepsis_detection_rate: float
    alert_response_time_min: float
    false_positive_rate: float
    model_uptime_pct: float
    predictions_per_day: int
    avg_risk_score: float
    icu_length_of_stay_proxy: float
    readmission_risk_proxy: float
    details: dict[str, Any] = Field(default_factory=dict)
