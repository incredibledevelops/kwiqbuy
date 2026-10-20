"""
Lightweight in-process WebSocket broker for the kitchen display.

All connected kitchen clients subscribe to a single channel ("kitchen").
When an order changes status, we broadcast the new order to every client.
"""
import asyncio
import json
import logging
from typing import Any, Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class KitchenBroker:
    def __init__(self):
        self._clients: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)
        logger.info("[ws] kitchen client connected (%d total)", len(self._clients))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)
        logger.info("[ws] kitchen client disconnected (%d left)", len(self._clients))

    async def broadcast(self, event: str, payload: Dict[str, Any]) -> None:
        if not self._clients:
            return
        message = json.dumps({"event": event, "payload": payload}, default=str)

        dead: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            await self.disconnect(ws)


kitchen_broker = KitchenBroker()


async def broadcast_order_event(event: str, order_payload: Dict[str, Any]) -> None:
    """
    Fire-and-forget broadcast. Never raise — the caller should not fail
    if broadcasting fails.
    """
    try:
        await kitchen_broker.broadcast(event, order_payload)
    except Exception:
        logger.exception("[ws] broadcast failed")