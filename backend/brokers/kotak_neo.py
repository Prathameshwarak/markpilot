"""Kotak Neo broker adapter (read-only scaffold for V1).

- Credentials are read from environment variables ONLY (never hardcoded, never logged,
  never exposed to the frontend).
- No order-placement method exists in V1.
- Live connectivity is NOT implemented yet; methods return a clear 'not_connected'
  status so the UI can show broker state without any real Kotak session. The current
  Kotak Neo SDK wiring will be added in a later milestone against live documentation.
"""
from __future__ import annotations
import os
import logging

from brokers.base import BrokerAdapter

logger = logging.getLogger(__name__)

# Only variables actually required by the current adapter scaffold are referenced.
_KOTAK_ENV_KEYS = [
    "KOTAK_API_KEY", "KOTAK_API_SECRET", "KOTAK_CONSUMER_KEY", "KOTAK_CONSUMER_SECRET",
    "KOTAK_UCC", "KOTAK_MOBILE", "KOTAK_MPIN", "KOTAK_TOTP_SECRET",
]


class KotakNeoAdapter(BrokerAdapter):
    def __init__(self):
        # Store presence flags only; never retain or log the secret values themselves.
        self._configured = all(os.environ.get(k) for k in _KOTAK_ENV_KEYS)
        self._session = None

    def _not_connected(self, action: str) -> dict:
        return {"status": "not_connected", "action": action,
                "configured": self._configured,
                "message": "Kotak Neo live connection not implemented in V1."}

    def authenticate(self) -> dict:
        # Do NOT log credentials. Only whether configuration is present.
        logger.info("Kotak Neo authenticate() called (configured=%s)", self._configured)
        return self._not_connected("authenticate")

    def get_quote(self, symbol: str) -> dict:
        return self._not_connected("get_quote")

    def get_historical_data(self, symbol: str, interval: str = "day", days: int = 120) -> dict:
        return self._not_connected("get_historical_data")

    def subscribe_market_data(self, symbols: list[str]) -> dict:
        return self._not_connected("subscribe_market_data")

    def unsubscribe_market_data(self, symbols: list[str]) -> dict:
        return self._not_connected("unsubscribe_market_data")

    def health_check(self) -> dict:
        return {
            "broker": "kotak_neo",
            "configured": self._configured,
            "connected": False,
            "order_execution": "disabled",  # never enabled in V1
        }
