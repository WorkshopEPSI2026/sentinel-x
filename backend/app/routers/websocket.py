from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket import alerts_manager, manager


router = APIRouter()


@router.websocket("/ws/telemetry")
async def telemetry_websocket(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await alerts_manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        alerts_manager.disconnect(websocket)
