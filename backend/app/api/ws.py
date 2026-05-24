import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, task_id: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(task_id, []).append(ws)

    def disconnect(self, task_id: str, ws: WebSocket):
        conns = self._connections.get(task_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, task_id: str, message: dict):
        for ws in self._connections.get(task_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def broadcast_log(self, task_id: str, level: str, message: str):
        await self.broadcast(task_id, {
            "type": "log", "level": level, "message": message,
        })


manager = ConnectionManager()


@router.websocket("/ws/tasks/{task_id}")
async def task_websocket(ws: WebSocket, task_id: str):
    await manager.connect(task_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id, ws)
