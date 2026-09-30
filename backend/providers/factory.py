"""Market-data provider selection.

MARKET_DATA_PROVIDER=mock  -> deterministic MockMarketDataProvider (default; used by tests)
MARKET_DATA_PROVIDER=kotak -> KotakMarketDataProvider, only when Kotak is fully configured;
                              otherwise we transparently fall back to mock (never pretend).
"""
from __future__ import annotations

from config import settings
from providers.mock import MockMarketDataProvider
from providers.kotak_provider import KotakMarketDataProvider
from brokers.registry import get_kotak_adapter


def get_market_data_provider():
    if settings.MARKET_DATA_PROVIDER == "kotak" and settings.kotak_configured():
        return KotakMarketDataProvider(get_kotak_adapter()), "kotak"
    return MockMarketDataProvider(), "mock"
