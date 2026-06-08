"""Realtime intelligence API routes — SSE, WebSocket, executive dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from premonition.api.dependencies import RealtimeSvcDep
from premonition.api.security import verify_api_key
from premonition.realtime.schemas import ExecutiveSummary, PatientMonitorState, PriorityRanking

router = APIRouter(tags=["Realtime"], dependencies=[Depends(verify_api_key)])


@router.get(
    "/realtime/executive",
    response_model=ExecutiveSummary,
    summary="Executive command center summary",
    description="CEO dashboard KPIs: patients, alerts, risk, model accuracy.",
)
async def executive_summary(service: RealtimeSvcDep) -> ExecutiveSummary:
    return service.get_executive_summary()


@router.get(
    "/realtime/patients",
    response_model=list[PatientMonitorState],
    summary="Live monitored patients",
    description="Current state of all ICU patients under realtime monitoring.",
)
async def live_patients(service: RealtimeSvcDep) -> list[PatientMonitorState]:
    return service.get_patients()


@router.get(
    "/realtime/patients/{patient_id}",
    response_model=PatientMonitorState,
    summary="Single patient monitor state",
)
async def live_patient(patient_id: str, service: RealtimeSvcDep) -> PatientMonitorState:
    from fastapi import HTTPException

    state = service.get_patient(patient_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not monitored")
    return state


@router.post(
    "/realtime/patients/{patient_id}/acknowledge",
    summary="Acknowledge patient alerts",
)
async def acknowledge_alert(patient_id: str, service: RealtimeSvcDep) -> dict:
    service.acknowledge_patient(patient_id)
    return {"status": "acknowledged", "patient_id": patient_id}


@router.get(
    "/realtime/priority",
    response_model=PriorityRanking,
    summary="Patient priority rankings",
    description="Top 10 critical, escalating, and stable patients.",
)
async def priority_ranking(service: RealtimeSvcDep) -> PriorityRanking:
    return service.get_priority_ranking()


@router.get(
    "/realtime/alerts",
    summary="Alert audit trail",
    description="Recent alerts with timestamp, patient, risk, confidence, reason.",
)
async def alert_history(service: RealtimeSvcDep, limit: int = 100) -> dict:
    items = service.get_alert_history(limit=limit)
    return {"count": len(items), "items": items}


@router.get(
    "/realtime/notifications",
    summary="Recent notifications",
)
async def recent_notifications(service: RealtimeSvcDep, limit: int = 50) -> dict:
    items = service.get_notifications(limit=limit)
    return {"count": len(items), "items": items}


@router.get(
    "/realtime/status",
    summary="Realtime engine status",
)
async def realtime_status(service: RealtimeSvcDep) -> dict:
    return {
        "running": service.is_running,
        "connections": service.connection_count,
        "patients_monitored": len(service.get_patients()),
    }


@router.get(
    "/realtime/stream",
    summary="SSE event stream",
    description="Server-Sent Events stream for live dashboard updates.",
)
async def sse_stream(request: Request, service: RealtimeSvcDep) -> StreamingResponse:
    queue = await service.hub.subscribe_sse()
    return StreamingResponse(
        service.hub.sse_generator(queue, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.websocket("/realtime/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for bidirectional realtime updates."""
    hub = websocket.app.state.streaming_hub
    await hub.connect_ws(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await hub.handle_ws_message(websocket, message)
    except WebSocketDisconnect:
        await hub.disconnect_ws(websocket)
