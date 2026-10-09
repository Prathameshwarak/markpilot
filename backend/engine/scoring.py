"""Combines the 5 transparent components into a single 100-point Opportunity Score."""
from __future__ import annotations


def opportunity_score(technical: dict, fundamental: dict, sentiment: dict, sector: dict, risk_reward: dict) -> dict:
    parts = {
        "technical": technical,
        "fundamental": fundamental,
        "sentiment": sentiment,
        "sector": sector,
        "risk_reward": risk_reward,
    }
    total = sum(p["score"] for p in parts.values())
    return {
        "total": int(total),
        "max": 100,
        "breakdown": {k: {"score": v["score"], "max": v["max"]} for k, v in parts.items()},
        "components": parts,
    }


def market_regime(nifty_close: list[float]) -> dict:
    """Deterministic Bullish / Neutral / Bearish from price vs EMAs, momentum and volatility."""
    from engine.technical import ema, price_momentum
    import numpy as np

    price = nifty_close[-1]
    e20 = ema(nifty_close, 20)
    e50 = ema(nifty_close, 50)
    mom = price_momentum(nifty_close, 10) or 0
    if len(nifty_close) >= 21:
        window = np.asarray(nifty_close[-21:], dtype="float64")
        vol = float(np.std(np.diff(window) / window[:-1]) * 100)
    else:
        vol = 0.0

    score = 0
    if e20 and price > e20:
        score += 1
    if e50 and price < e50:
        score -= 1
    elif e50 and price > e50:
        score += 1
    score += 1 if mom > 1 else -1 if mom < -1 else 0

    regime = "BULLISH" if score >= 2 else "BEARISH" if score <= -1 else "NEUTRAL"
    return {
        "regime": regime,
        "factors": {
            "price_vs_ema20": "above" if e20 and price > e20 else "below",
            "price_vs_ema50": "above" if e50 and price > e50 else "below",
            "momentum_pct": round(mom, 2),
            "volatility_pct": round(vol, 2),
        },
    }
