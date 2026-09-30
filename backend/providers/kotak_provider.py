"""KotakMarketDataProvider — implements MarketDataProvider over the read-only Kotak adapter,
returning the same columnar OHLCV / quote shapes the research engine already expects.

On failure it raises (never silently substitutes fake data); callers decide fallback.
Lightweight TTL caching avoids hammering the broker API.
"""
from __future__ import annotations
from datetime import datetime, timezone

import cache
from config import settings
from providers.base import MarketDataProvider
from brokers import instruments


class KotakMarketDataProvider(MarketDataProvider):
    def __init__(self, adapter):
        self._adapter = adapter

    def get_quote(self, symbol: str) -> dict:
        ck = f"kquote:{symbol}"
        cached = cache.get(ck)
        if cached:
            return cached
        q = self._adapter.get_quote(symbol)  # normalized dict from adapter
        out = {
            "symbol": symbol,
            "price": q.get("ltp"),
            "change_pct": q.get("change_pct"),
            "volume": q.get("volume"),
            "stale": not q.get("is_live", False),
            "is_live": bool(q.get("is_live", False)),
            "timestamp": q.get("timestamp"),
            "source": "kotak",
        }
        cache.set(ck, out, settings.QUOTE_CACHE_TTL)
        return out

    def get_historical(self, symbol: str, days: int = 120) -> dict:
        ck = f"khist:{symbol}:{days}"
        cached = cache.get(ck)
        if cached:
            return cached
        candles = self._adapter.get_historical_data(symbol, interval="day", days=days)
        if not candles or len(candles) < 60:
            raise RuntimeError("INSUFFICIENT_DATA")
        columnar = {
            "open": [c["open"] for c in candles],
            "high": [c["high"] for c in candles],
            "low": [c["low"] for c in candles],
            "close": [c["close"] for c in candles],
            "volume": [c["volume"] for c in candles],
        }
        cache.set(ck, columnar, settings.HISTORICAL_CACHE_TTL)
        return columnar

    def get_index(self, index: str = "NIFTY") -> dict:
        tok = instruments.index_token(index)
        if not tok:
            raise RuntimeError("Unknown index")
        exchange, token = tok
        candles = self._adapter.get_historical_data(index, interval="day", days=120)
        close = [c["close"] for c in candles] if candles else []
        if len(close) < 21:
            raise RuntimeError("INSUFFICIENT_DATA")
        return {
            "index": index,
            "value": round(close[-1], 2),
            "change_pct": round((close[-1] / close[-2] - 1) * 100, 2),
            "close": close,
            "source": "kotak",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
