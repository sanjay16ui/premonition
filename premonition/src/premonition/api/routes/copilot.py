"""Clinical AI Copilot API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from premonition.api.dependencies import CopilotSvcDep
from premonition.auth.dependencies import AuthCtxDep, require_perm
from premonition.copilot.schemas import (
    ChatRequest,
    CopilotRecommendationsRequest,
    ExecutiveSummaryRequest,
    ExplainAlertRequest,
    ExplainPredictionRequest,
    HandoverRequest,
    IngestDocumentRequest,
    PatientSummaryRequest,
    SearchRequest,
)

router = APIRouter(prefix="/copilot", tags=["Clinical AI Copilot"])


@router.post("/chat", dependencies=[Depends(require_perm("copilot:use"))])
async def copilot_chat(body: ChatRequest, svc: CopilotSvcDep, auth: AuthCtxDep) -> dict:
    return await svc.chat(body, auth)


@router.post("/explain-prediction", dependencies=[Depends(require_perm("copilot:use"))])
async def copilot_explain_prediction(body: ExplainPredictionRequest, svc: CopilotSvcDep, auth: AuthCtxDep) -> dict:
    return await svc.explain_prediction(body, auth)


@router.post("/explain-alert", dependencies=[Depends(require_perm("copilot:use"))])
async def copilot_explain_alert(body: ExplainAlertRequest, svc: CopilotSvcDep, auth: AuthCtxDep) -> dict:
    return await svc.explain_alert(body, auth)


@router.post("/patient-summary", dependencies=[Depends(require_perm("copilot:use"))])
async def copilot_patient_summary(body: PatientSummaryRequest, svc: CopilotSvcDep, auth: AuthCtxDep) -> dict:
    return await svc.patient_summary(body, auth)


@router.post("/handover", dependencies=[Depends(require_perm("copilot:use"))])
async def copilot_handover(body: HandoverRequest, svc: CopilotSvcDep, auth: AuthCtxDep) -> dict:
    return await svc.handover(body, auth)


@router.post("/executive-summary", dependencies=[Depends(require_perm("copilot:executive"))])
async def copilot_executive_summary(body: ExecutiveSummaryRequest, svc: CopilotSvcDep, auth: AuthCtxDep) -> dict:
    return await svc.executive_summary(body, auth)


@router.post("/recommendations", dependencies=[Depends(require_perm("copilot:use"))])
async def copilot_recommendations(body: CopilotRecommendationsRequest, svc: CopilotSvcDep, auth: AuthCtxDep) -> dict:
    return await svc.recommendations(body, auth)


@router.post("/ingest-document", dependencies=[Depends(require_perm("copilot:ingest"))])
async def copilot_ingest(body: IngestDocumentRequest, svc: CopilotSvcDep, auth: AuthCtxDep) -> dict:
    return await svc.ingest_document(body, auth)


@router.post("/search", dependencies=[Depends(require_perm("copilot:use"))])
async def copilot_search(body: SearchRequest, svc: CopilotSvcDep) -> dict:
    return await svc.search(body)


@router.get("/conversations", dependencies=[Depends(require_perm("copilot:read"))])
async def copilot_list_conversations(svc: CopilotSvcDep, auth: AuthCtxDep) -> list[dict]:
    return await svc.list_conversations(auth)


@router.get("/conversations/{conversation_id}", dependencies=[Depends(require_perm("copilot:read"))])
async def copilot_get_conversation(conversation_id: str, svc: CopilotSvcDep) -> dict:
    result = await svc.get_conversation(conversation_id)
    if not result:
        raise HTTPException(404, "Conversation not found")
    return result
