"""Abstract data-provider interfaces. The Equity engine depends on these, not on any
concrete vendor, so Yahoo / NSE / broker feeds can be swapped in later.
"""
from __future__ import annotations
from abc import ABC, abstractmethod


class MarketDataProvider(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> dict: ...

    @abstractmethod
    def get_historical(self, symbol: str, days: int = 120) -> dict:
        """Return OHLCV dict: {'open','high','low','close','volume'} as equal-length lists."""

    @abstractmethod
    def get_index(self, index: str = "NIFTY") -> dict: ...


class FundamentalDataProvider(ABC):
    @abstractmethod
    def get_fundamentals(self, symbol: str) -> dict: ...


class NewsProvider(ABC):
    @abstractmethod
    def get_news(self, symbol: str) -> list[dict]:
        """Return list of {'headline','source','timestamp'}."""


class SentimentProvider(ABC):
    @abstractmethod
    def score(self, headlines: list[str], direction: str = "bullish") -> dict: ...
