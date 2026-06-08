"""Model version and metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from premonition.api.dependencies import ModelDep
from premonition.api.schemas.responses import ModelVersionResponse
from premonition.api.security import verify_api_key

router = APIRouter(tags=["Models"], dependencies=[Depends(verify_api_key)])


@router.get(
    "/models/version",
    response_model=ModelVersionResponse,
    summary="Model version",
    description="Returns loaded model version, feature set, and training metrics.",
)
async def model_version(model_loader: ModelDep) -> ModelVersionResponse:
    version = model_loader.get_version_info()
    metadata = model_loader.state.metadata

    return ModelVersionResponse(
        model_name=version.get("model_name", metadata.get("model_name", "unknown")),
        model_version=version.get("model_version", metadata.get("model_version", "unknown")),
        tier=version.get("tier", model_loader.state.tier),
        training_timestamp=version.get("training_timestamp") or metadata.get("trained_at"),
        dataset_hash=version.get("dataset_version", {}).get("content_hash")
        if isinstance(version.get("dataset_version"), dict)
        else metadata.get("dataset_hash"),
        n_features=len(version.get("feature_set", metadata.get("feature_names", []))),
        feature_set=version.get("feature_set", metadata.get("feature_names", [])),
        metrics=metadata.get("metrics", version.get("metrics", {})),
    )
