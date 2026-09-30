"""Deterministic mock providers for V1. Seeded per-symbol so scores are stable across runs.

Real providers (yfinance/NSE) will implement the same interfaces in the next milestone.
"""
from __future__ import annotations
import hashlib
from datetime import datetime, timezone, timedelta
import numpy as np

from providers.base import MarketDataProvider, FundamentalDataProvider, NewsProvider, SentimentProvider
from engine.sentiment import sentiment_score
from data.universe import UNIVERSE, NEWS_TEMPLATES


def _seed(symbol: str) -> int:
    return int(hashlib.md5(symbol.encode()).hexdigest(), 16) % (2 ** 32)


def _gen_candles(symbol: str, base_price: float, drift: float, days: int = 120) -> dict:
    rng = np.random.default_rng(_seed(symbol))
    returns = rng.normal(drift, 0.015, days)
    close = base_price * np.cumprod(1 + returns)
    high = close * (1 + np.abs(rng.normal(0, 0.008, days)))
    low = close * (1 - np.abs(rng.normal(0, 0.008, days)))
    open_ = close * (1 + rng.normal(0, 0.005, days))
    volume = rng.integers(500_000, 5_000_000, days).astype(float)
    volume[-1] *= 1.4  # recent volume spike for realism
    return {
        "open": [round(x, 2) for x in open_],
        "high": [round(x, 2) for x in high],
        "low": [round(x, 2) for x in low],
        "close": [round(x, 2) for x in close],
        "volume": [float(v) for v in volume],
    }


class MockMarketDataProvider(MarketDataProvider):
    def get_historical(self, symbol: str, days: int = 120) -> dict:
        meta = UNIVERSE[symbol]
        return _gen_candles(symbol, meta["base_price"], meta["drift"], days)

    def get_quote(self, symbol: str) -> dict:
        c = self.get_historical(symbol)
        close = c["close"]
        change = (close[-1] / close[-2] - 1) * 100
        return {
            "symbol": symbol,
            "price": close[-1],
            "change_pct": round(change, 2),
            "volume": c["volume"][-1],
            "stale": False,
        }

    def get_index(self, index: str = "NIFTY") -> dict:
        c = _gen_candles(index, 24200, 0.0007, 120)
        close = c["close"]
        return {
            "index": index,
            "value": round(close[-1], 2),
            "change_pct": round((close[-1] / close[-2] - 1) * 100, 2),
            "close": close,
        }


class MockFundamentalDataProvider(FundamentalDataProvider):
    def get_fundamentals(self, symbol: str) -> dict:
        return UNIVERSE[symbol]["fundamentals"]


class MockNewsProvider(NewsProvider):
    def get_news(self, symbol: str) -> list[dict]:
        rng = np.random.default_rng(_seed(symbol) + 7)
        company = UNIVERSE[symbol]["name"]
        chosen = rng.choice(len(NEWS_TEMPLATES), size=4, replace=False)
        now = datetime.now(timezone.utc)
        out = []
        for i, idx in enumerate(chosen):
            tmpl = NEWS_TEMPLATES[int(idx)]
            out.append({
                "headline": tmpl["headline"].format(company=company),
                "source": tmpl["source"],
                "timestamp": (now - timedelta(hours=i * 6 + 1)).isoformat(),
            })
        return out


class LexiconSentimentProvider(SentimentProvider):
    def score(self, headlines: list[str], direction: str = "bullish") -> dict:
        return sentiment_score(headlines, direction)
