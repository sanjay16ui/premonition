"""Analytics API routes — enterprise intelligence platform."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from premonition.analytics.schemas import (
    CohortAnalysisRequest,
    OutcomePredictionRequest,
    RecommendationRequest,
    RiskStratificationRequest,
    SimulateRequest,
)
from premonition.api.dependencies import AnalyticsSvcDep
from premonition.api.security import verify_api_key

router = APIRouter(prefix="/analytics", tags=["Analytics"], dependencies=[Depends(verify_api_key)])


@router.get("/executive")
async def analytics_executive(svc: AnalyticsSvcDep) -> dict:
    """Executive dashboard intelligence — KPIs, alerts, risk overview."""
    return await svc.get_executive()


@router.get("/population")
async def analytics_population(svc: AnalyticsSvcDep) -> dict:
    """Population health metrics and sepsis incidence."""
    return await svc.get_population()


@router.get("/cohorts")
async def analytics_cohorts(svc: AnalyticsSvcDep, segment_by: str = "age_group") -> list[dict]:
    """Cohort segmentation analysis."""
    return await svc.get_cohorts(CohortAnalysisRequest(segment_by=segment_by))


@router.get("/outcomes")
async def analytics_outcomes(svc: AnalyticsSvcDep, horizon_hours: int = 24) -> list[dict]:
    """Outcome forecasting overview."""
    return await svc.get_outcomes(OutcomePredictionRequest(horizon_hours=horizon_hours))


@router.get("/capacity")
async def analytics_capacity(svc: AnalyticsSvcDep) -> dict:
    """ICU capacity and occupancy forecasting."""
    return await svc.get_capacity()


@router.get("/resources")
async def analytics_resources(svc: AnalyticsSvcDep) -> dict:
    """Resource utilization analytics."""
    return await svc.get_resources()


@router.get("/kpis")
async def analytics_kpis(svc: AnalyticsSvcDep) -> dict:
    """Hospital-wide KPI dashboard."""
    return await svc.get_kpis()


@router.post("/simulate")
async def analytics_simulate(body: SimulateRequest, svc: AnalyticsSvcDep) -> dict:
    """Simulate ICU surge or sepsis outbreak scenarios."""
    return await svc.simulate(body)


@router.post("/compare-models")
async def analytics_compare_models(svc: AnalyticsSvcDep) -> dict:
    """Compare LR vs RF vs XGBoost performance."""
    return await svc.compare_models()


@router.post("/recommendations")
async def analytics_recommendations(body: RecommendationRequest, svc: AnalyticsSvcDep) -> list[dict]:
    """Ranked clinical recommendations."""
    return await svc.get_recommendations(body)


@router.post("/risk-stratification")
async def analytics_risk_stratification(
    svc: AnalyticsSvcDep,
    body: RiskStratificationRequest | None = None,
) -> dict:
    """Stratify patients into risk tiers."""
    return await svc.risk_stratification(body)


@router.post("/cohort-analysis")
async def analytics_cohort_analysis(body: CohortAnalysisRequest, svc: AnalyticsSvcDep) -> list[dict]:
    """Detailed cohort segmentation analysis."""
    return await svc.cohort_analysis(body)


@router.post("/outcome-prediction")
async def analytics_outcome_prediction(body: OutcomePredictionRequest, svc: AnalyticsSvcDep) -> list[dict]:
    """Predict clinical outcomes for a patient."""
    return await svc.outcome_prediction(body)
