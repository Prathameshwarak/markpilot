"""BrokerAdapter interface. V1 defines the contract only.

IMPORTANT: place_order() is intentionally NOT part of the V1 interface and is never
called anywhere. The architecture is ready for future order execution, but MarketPilot
is a research/monitoring product, not an automated trading bot.
"""
from __future__ import annotations
from abc import ABC, abstractmethod


class BrokerAdapter(ABC):
    """Read-only broker contract for V1 (quotes, history, market-data streaming, health)."""

    @abstractmethod
    def authenticate(self) -> dict:
        """Establish an authenticated session using env-provided credentials."""

    @abstractmethod
    def get_quote(self, symbol: str) -> dict: ...

    @abstractmethod
    def get_historical_data(self, symbol: str, interval: str = "day", days: int = 120) -> dict: ...

    @abstractmethod
    def subscribe_market_data(self, symbols: list[str]) -> dict: ...

    @abstractmethod
    def unsubscribe_market_data(self, symbols: list[str]) -> dict: ...

    @abstractmethod
    def health_check(self) -> dict:
        """Return connectivity/auth status without exposing any credentials."""

    # NOTE: place_order() is deliberately omitted in V1. A future milestone may add:
    #   def place_order(self, order: dict) -> dict: ...
    # It must never be wired into monitoring/alerts automatically.
