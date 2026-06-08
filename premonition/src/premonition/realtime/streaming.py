"""Streaming Data Layer — SSE and WebSocket hub."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import WebSocket
from starlette.requests import Request

from premonition.realtime.config import RealtimeSettings
from premonition.realtime.schemas import RealtimeEvent
from premonition.utils.logging import get_logger
from premonition.utils.serialization import dumps_json

logger = get_logger(__name__)


class StreamingHub:
    """
    Production streaming hub supporting SSE and WebSocket.

    - SSE: one-way broadcast to dashboard clients
    - WebSocket: bidirectional with patient subscription
    """

    def __init__(self, settings: RealtimeSettings | None = None) -> None:
        self.settings = settings or RealtimeSettings.from_env()
        self._sse_queues: list[asyncio.Queue[RealtimeEvent | None]] = []
        self._ws_clients: list[WebSocket] = []
        self._ws_subscriptions: dict[WebSocket, set[str]] = {}
        self._lock = asyncio.Lock()

    @property
    def connection_count(self) -> int:
        return len(self._sse_queues) + len(self._ws_clients)

    async def subscribe_sse(self) -> asyncio.Queue[RealtimeEvent | None]:
        if self.connection_count >= self.settings.max_connections:
            raise RuntimeError("Max streaming connections reached")
        queue: asyncio.Queue[RealtimeEvent | None] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._sse_queues.append(queue)
        return queue

    async def unsubscribe_sse(self, queue: asyncio.Queue[RealtimeEvent | None]) -> None:
        async with self._lock:
            if queue in self._sse_queues:
                self._sse_queues.remove(queue)

    async def connect_ws(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._ws_clients.append(ws)
            self._ws_subscriptions[ws] = set()

    async def disconnect_ws(self, ws: WebSocket) -> None:
        async with self._lock:
            if ws in self._ws_clients:
                self._ws_clients.remove(ws)
            self._ws_subscriptions.pop(ws, None)

    async def subscribe_patient(self, ws: WebSocket, patient_id: str) -> None:
        if ws in self._ws_subscriptions:
            self._ws_subscriptions[ws].add(patient_id)

    async def broadcast(self, event: RealtimeEvent) -> None:
        async with self._lock:
            dead_sse: list[asyncio.Queue] = []
            for q in self._sse_queues:
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    dead_sse.append(q)
            for q in dead_sse:
                self._sse_queues.remove(q)

            dead_ws: list[WebSocket] = []
            payload = dumps_json(event.model_dump())
            patient_id = event.data.get("patient_id") or (
                event.data.get("patient", {}).get("patient_id")
                if isinstance(event.data.get("patient"), dict)
                else None
            )
            for ws in self._ws_clients:
                subs = self._ws_subscriptions.get(ws, set())
                if subs and patient_id and patient_id not in subs:
                    continue
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_ws.append(ws)
            for ws in dead_ws:
                await self.disconnect_ws(ws)

    async def sse_generator(
        self,
        queue: asyncio.Queue[RealtimeEvent | None],
        request: Request,
    ) -> AsyncIterator[str]:
        """Yield Server-Sent Events."""
        try:
            yield f"event: connected\ndata: {dumps_json({'status': 'connected'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=self.settings.sse_heartbeat_seconds,
                    )
                except asyncio.TimeoutError:
                    yield f"event: heartbeat\ndata: {dumps_json({'ts': 'ping'})}\n\n"
                    continue
                if event is None:
                    break
                yield f"event: {event.event_type}\ndata: {dumps_json(event.model_dump())}\n\n"
        finally:
            await self.unsubscribe_sse(queue)

    async def handle_ws_message(self, ws: WebSocket, message: str) -> None:
        try:
            data = json.loads(message)
            action = data.get("action")
            if action == "subscribe" and "patient_id" in data:
                await self.subscribe_patient(ws, str(data["patient_id"]))
                await ws.send_text(dumps_json({"event": "subscribed", "patient_id": data["patient_id"]}))
            elif action == "subscribe_all":
                self._ws_subscriptions[ws] = set()
                await ws.send_text(dumps_json({"event": "subscribed_all"}))
            elif action == "ping":
                await ws.send_text(dumps_json({"event": "pong"}))
        except json.JSONDecodeError:
            await ws.send_text(dumps_json({"event": "error", "message": "Invalid JSON"}))

    async def shutdown(self) -> None:
        async with self._lock:
            for q in self._sse_queues:
                await q.put(None)
            self._sse_queues.clear()
            for ws in list(self._ws_clients):
                try:
                    await ws.close()
                except Exception:
                    pass
            self._ws_clients.clear()
            self._ws_subscriptions.clear()
