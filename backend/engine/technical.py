"""Deterministic technical-analysis primitives and transparent technical score.

No LLM is ever used here. Every function is pure and unit-testable.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def _series(x) -> pd.Series:
    return pd.Series(list(x), dtype="float64")


def ema(values, period: int):
    s = _series(values)
    if len(s) < 1:
        return None
    return float(s.ewm(span=period, adjust=False).mean().iloc[-1])


def rsi(values, period: int = 14):
    s = _series(values)
    if len(s) <= period:
        return None
    delta = s.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi_series = rsi_series.fillna(100)  # no losses -> fully overbought
    return float(rsi_series.iloc[-1])


def atr(high, low, close, period: int = 14):
    h, l, c = _series(high), _series(low), _series(close)
    if len(c) <= period:
        return None
    prev_close = c.shift(1)
    tr = pd.concat([(h - l), (h - prev_close).abs(), (l - prev_close).abs()], axis=1).max(axis=1)
    atr_series = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return float(atr_series.iloc[-1])


def volume_ratio(volumes, period: int = 20):
    s = _series(volumes)
    if len(s) < 2:
        return None
    window = s.iloc[-period - 1:-1] if len(s) > period else s.iloc[:-1]
    avg = window.mean()
    if not avg or np.isnan(avg):
        return None
    return float(s.iloc[-1] / avg)


def price_momentum(close, period: int = 10):
    s = _series(close)
    if len(s) <= period:
        return None
    return float((s.iloc[-1] / s.iloc[-1 - period] - 1) * 100)


def support_resistance(low, high, window: int = 20):
    l, h = _series(low), _series(high)
    support = float(l.iloc[-window:].min())
    resistance = float(h.iloc[-window:].max())
    return support, resistance


def analyze(candles: dict) -> dict:
    """candles: {'open','high','low','close','volume'} lists. Returns indicator dict."""
    close = candles["close"]
    support, resistance = support_resistance(candles["low"], candles["high"])
    return {
        "price": float(close[-1]),
        "ema20": ema(close, 20),
        "ema50": ema(close, 50),
        "rsi": rsi(close, 14),
        "atr": atr(candles["high"], candles["low"], close, 14),
        "volume_ratio": volume_ratio(candles["volume"], 20),
        "momentum": price_momentum(close, 10),
        "support": support,
        "resistance": resistance,
    }


def technical_score(ind: dict, direction: str = "bullish") -> dict:
    """Transparent technical score out of 35: trend(10) momentum(10) volume(10) volatility(5)."""
    price, e20, e50 = ind.get("price"), ind.get("ema20"), ind.get("ema50")
    rsi_v, mom, vr, atr_v = ind.get("rsi"), ind.get("momentum"), ind.get("volume_ratio"), ind.get("atr")
    comps = {}

    trend = 0
    if e20 is not None and e50 is not None:
        if direction == "bullish":
            trend += 5 if price > e20 else 0
            trend += 5 if e20 > e50 else 0
        else:
            trend += 5 if price < e20 else 0
            trend += 5 if e20 < e50 else 0
    comps["trend"] = trend

    m = 0
    if rsi_v is not None:
        if direction == "bullish":
            m += 6 if 55 <= rsi_v <= 72 else 4 if 48 <= rsi_v < 55 else 3 if rsi_v > 72 else 1
        else:
            m += 6 if 28 <= rsi_v <= 45 else 4 if 45 < rsi_v <= 52 else 3 if rsi_v < 28 else 1
    if mom is not None:
        if direction == "bullish" and mom > 0:
            m += min(4, round(mom / 2))
        elif direction == "bearish" and mom < 0:
            m += min(4, round(abs(mom) / 2))
    comps["momentum"] = min(10, m)

    v = 0
    if vr is not None:
        v = 10 if vr >= 1.5 else 7 if vr >= 1.2 else 4 if vr >= 1.0 else 2
    comps["volume"] = v

    vol = 0
    if atr_v is not None and price:
        atr_pct = atr_v / price * 100
        vol = 5 if atr_pct <= 2 else 3 if atr_pct <= 3.5 else 1
    comps["volatility"] = vol

    total = comps["trend"] + comps["momentum"] + comps["volume"] + comps["volatility"]
    return {"score": int(total), "max": 35, "components": comps}
