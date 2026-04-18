from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database import get_db
from schemas import DetectionRequest, DetectionResponse
from services.detection_engine import run_detection
from websocket_manager import manager

router = APIRouter(prefix="/detection", tags=["detection"])


@router.post("/run", response_model=DetectionResponse)
async def run_detection_endpoint(
    payload: DetectionRequest,
    db: Session = Depends(get_db),
):
    result = run_detection(
        charger_id=payload.charger_id,
        live_certificate_pem=payload.live_certificate_pem,
        live_latency_ms=payload.live_latency_ms,
        live_billing_rate=payload.live_billing_rate,
        live_timing_ms=payload.live_timing_ms,
        db=db,
    )

    await manager.broadcast({
        "event": "trust_score_update",
        "charger_id": payload.charger_id,
        "score": result.score,
        "status": result.status,
        "action": result.action,
        "hard_blocked": result.hard_blocked,
        "explanation": result.confidence_explanation,
    })

    return DetectionResponse(
        charger_id=payload.charger_id,
        score=result.score,
        status=result.status,
        action=result.action,
        hard_blocked=result.hard_blocked,
        confidence_explanation=result.confidence_explanation,
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)