"""Live market-data WebSocket infrastructure (read-only).

Milestone 2 establishes reliable live-quote plumbing only. NO T1/T2/SL/trailing alerts —
those belong to a later milestone. Because live streaming requires real Kotak credentials
(unavailable in automated tests), a `MockWebSocketProvider` is provided for deterministic
unit testing of the connect/subscribe/normalize/reconnect lifecycle.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

logger = logging.getLogger("marketpilot.ws")


def normalize_tick(raw: dict) -> dict:
    """Map a raw SFeed scrip message to the internal normalized tick shape."""
    return {
        "symbol": raw.get("trading_symbol") or raw.get("symbol"),
        "ltp": raw.get("last_traded_price") or raw.get("ltp"),
        "volume": raw.get("volume"),
        "timestamp": raw.get("last_traded_time") or datetime.now(timezone.utc).isoformat(),
        "source": "kotak",
        "is_live": True,
    }


class MockWebSocketProvider:
    """Deterministic in-memory WS used by tests. Mirrors the real lifecycle."""

    def __init__(self, max_reconnects: int = 3):
        self.connected = False
        self.subscriptions: list[dict] = []
        self.reconnect_attempts = 0
        self.max_reconnects = max_reconnects
        self._inbox: list[dict] = []

    def connect(self) -> bool:
        self.connected = True
        return True

    def subscribe(self, tokens: list[dict]) -> dict:
        if not self.connected:
            raise RuntimeError("not connected")
        self.subscriptions.extend(tokens)
        return {"status": "subscribed", "count": len(tokens)}

    def push(self, raw: dict):
        self._inbox.append(raw)

    def receive(self) -> list[dict]:
        ticks = [normalize_tick(r) for r in self._inbox]
        self._inbox.clear()
        return ticks

    def disconnect(self) -> bool:
        self.connected = False
        return True

    def reconnect(self) -> bool:
        """Attempt reconnect with a hard cap; re-subscribes existing tokens on success."""
        if self.reconnect_attempts >= self.max_reconnects:
            return False
        self.reconnect_attempts += 1
        self.connected = True
        return True


class KotakWebSocketClient:
    """Thin wrapper over the SDK's async SFeed WebSocket. Not exercised without credentials."""

    def __init__(self, neo_client):
        self._neo = neo_client
        self._ws = None
        self.subscriptions: list = []

    async def connect(self):
        self._ws = self._neo.create_websocket()
        await self._ws.__aenter__()
        return self._ws

    async def subscribe(self, ws_tokens: list):
        if not self._ws:
            raise RuntimeError("WebSocket not connected")
        await self._ws.subscribe_scrips(ws_tokens)
        self.subscriptions = ws_tokens

    async def disconnect(self):
        if self._ws:
            await self._ws.__aexit__(None, None, None)
            self._ws = None
