"""MLOps routes — promotion, drift, monitoring."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from premonition.api.dependencies import get_app_settings
from premonition.auth.dependencies import AuthCtxDep, require_perm
from premonition.config.settings import Settings
from premonition.mlops.drift import DriftDetector
from premonition.mlops.monitoring import FeatureMonitor, PredictionMonitor
from premonition.mlops.promotion import ModelPromotionService

router = APIRouter(prefix="/mlops", tags=["MLOps"])

_promotion: ModelPromotionService | None = None
_feature_monitor = FeatureMonitor()
_prediction_monitor = PredictionMonitor()
_drift_detector = DriftDetector()


def get_promotion_service(settings: Annotated[Settings, Depends(get_app_settings)]) -> ModelPromotionService:
    global _promotion
    if _promotion is None:
        _promotion = ModelPromotionService(settings.models_dir)
    return _promotion


@router.get("/status", dependencies=[Depends(require_perm("mlops:manage"))])
async def mlops_status(
    settings: Annotated[Settings, Depends(get_app_settings)],
    promotion: Annotated[ModelPromotionService, Depends(get_promotion_service)],
) -> dict[str, Any]:
    tier = settings.primary_tier
    return {
        "tier": tier,
        "stages": promotion.get_stage_status(tier),
        "feature_monitor": _feature_monitor.summary(),
        "prediction_monitor": _prediction_monitor.summary(),
    }


@router.post("/promote/staging", dependencies=[Depends(require_perm("mlops:manage"))])
async def promote_staging(
    ctx: AuthCtxDep,
    promotion: Annotated[ModelPromotionService, Depends(get_promotion_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, Any]:
    return promotion.promote_to_staging(settings.default_tier, ctx.subject)


@router.post("/promote/production", dependencies=[Depends(require_perm("mlops:manage"))])
async def promote_production(
    ctx: AuthCtxDep,
    promotion: Annotated[ModelPromotionService, Depends(get_promotion_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, Any]:
    return promotion.approve_for_production(settings.primary_tier, ctx.subject)


@router.post("/rollback", dependencies=[Depends(require_perm("mlops:manage"))])
async def rollback(
    ctx: AuthCtxDep,
    promotion: Annotated[ModelPromotionService, Depends(get_promotion_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> dict[str, Any]:
    return promotion.rollback_production(settings.primary_tier, ctx.subject)


@router.get("/history", dependencies=[Depends(require_perm("models:read"))])
async def promotion_history(
    promotion: Annotated[ModelPromotionService, Depends(get_promotion_service)],
) -> list[dict[str, Any]]:
    return promotion.get_promotion_history()


@router.post("/drift/check", dependencies=[Depends(require_perm("mlops:manage"))])
async def check_drift(payload: dict[str, Any]) -> dict[str, Any]:
    report = _drift_detector.full_report(
        reference_features=payload.get("reference_features", {}),
        current_features=payload.get("current_features", {}),
        reference_scores=payload.get("reference_scores"),
        current_scores=payload.get("current_scores"),
        baseline_metrics=payload.get("baseline_metrics"),
        current_metrics=payload.get("current_metrics"),
    )
    return report.to_dict()
