"""Research service: composes providers + engine into equities, research snapshots,
trade ideas and market overview.

Provider is selected via config (mock by default; Kotak when configured). If a live build
fails, we log and fall back to deterministic mock data marked clearly as DEMO — we never
present fallback data as LIVE.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone

from providers.factory import get_market_data_provider
from providers.mock import (
    MockMarketDataProvider, MockFundamentalDataProvider, MockNewsProvider, LexiconSentimentProvider,
)
from brokers.registry import get_kotak_adapter
from data.universe import UNIVERSE, SECTORS
from engine import technical, fundamental, sector as sector_engine, risk, scoring
import market_status as mkt

logger = logging.getLogger("marketpilot.services")

_fund = MockFundamentalDataProvider()
_news = MockNewsProvider()
_sentiment = LexiconSentimentProvider()

# Module-level data-source state (updated by the build).
DATA_SOURCE = "mock"
DATA_QUALITY = "DEMO"
LAST_MARKET_DATA_TS = datetime.now(timezone.utc).isoformat()


def _sector_return(candles: dict) -> float:
    c = candles["close"]
    return (c[-1] / c[-21] - 1) * 100 if len(c) >= 21 else 0.0


def _build_one(symbol: str, provider, source: str, nifty_close: list[float]) -> dict:
    meta = UNIVERSE[symbol]
    candles = provider.get_historical(symbol)
    ind = technical.analyze(candles)
    direction = "bullish" if (ind["ema20"] and ind["price"] > ind["ema20"]) else "bearish"

    stock_ret = _sector_return(candles)
    nifty_ret = (nifty_close[-1] / nifty_close[-21] - 1) * 100
    sector_ret = stock_ret * 0.85 + nifty_ret * 0.15

    tech = technical.technical_score(ind, direction)
    fund = fundamental.fundamental_score(_fund.get_fundamentals(symbol))
    news = _news.get_news(symbol)
    sent = _sentiment.score([n["headline"] for n in news], direction)
    sect = sector_engine.sector_score(stock_ret, sector_ret, nifty_ret, direction)

    levels = risk.compute_levels(ind["price"], ind["atr"] or ind["price"] * 0.02, direction)
    rr = risk.risk_reward_score(levels["risk_reward"])
    opp = scoring.opportunity_score(tech, fund, sent, sect, rr)

    q = provider.get_quote(symbol)
    is_live = bool(q.get("is_live", False)) if source == "kotak" else False
    data_ts = q.get("timestamp") or datetime.now(timezone.utc).isoformat()
    # Technical data-quality flag: full history required for EMA50/ATR14.
    tech_status = "OK" if (ind["ema50"] is not None and ind["atr"] is not None) else "INSUFFICIENT_DATA"
    if source == "mock":
        data_quality = "DEMO"
    elif tech_status == "INSUFFICIENT_DATA":
        data_quality = "PARTIAL"
    else:
        data_quality = "LIVE" if is_live else "PARTIAL"

    return {
        "symbol": symbol,
        "company": meta["name"],
        "sector": meta["sector"],
        "price": ind["price"],
        "change_pct": q.get("change_pct") if q.get("change_pct") is not None else 0.0,
        "volume": candles["volume"][-1],
        "direction": direction,
        "data_source": source,
        "is_live": is_live,
        "data_timestamp": data_ts,
        "data_quality": data_quality,
        "technical_status": tech_status,
        "indicators": {
            "rsi": round(ind["rsi"], 2) if ind["rsi"] else None,
            "ema20": round(ind["ema20"], 2) if ind["ema20"] else None,
            "ema50": round(ind["ema50"], 2) if ind["ema50"] else None,
            "atr": round(ind["atr"], 2) if ind["atr"] else None,
            "volume_ratio": round(ind["volume_ratio"], 2) if ind["volume_ratio"] else None,
            "momentum": round(ind["momentum"], 2) if ind["momentum"] else None,
            "support": round(ind["support"], 2),
            "resistance": round(ind["resistance"], 2),
        },
        "scores": {
            "technical": tech["score"], "fundamental": fund["score"], "sentiment": sent["score"],
            "sector": sect["score"], "risk_reward": rr["score"], "overall": opp["total"],
        },
        "levels": levels,
        "opportunity": opp,
        "fundamentals": _fund.get_fundamentals(symbol),
        "news": news,
        "sector_analysis": sect["components"],
        "candles": candles,
    }


def _build_all(provider, source: str):
    nifty = provider.get_index("NIFTY")
    regime = scoring.market_regime(nifty["close"])
    equities = {sym: _build_one(sym, provider, source, nifty["close"]) for sym in UNIVERSE}
    return equities, regime, nifty


def _build_with_fallback():
    provider, source = get_market_data_provider()
    if source == "kotak":
        try:
            get_kotak_adapter().authenticate()
            eq, regime, nifty = _build_all(provider, source)
            logger.info("Research built from LIVE Kotak data.")
            return eq, regime, nifty, "kotak"
        except Exception as e:
            logger.warning("Kotak live build failed (%s); falling back to DEMO mock data.", type(e).__name__)
    eq, regime, nifty = _build_all(MockMarketDataProvider(), "mock")
    return eq, regime, nifty, "mock"


EQUITIES, _REGIME, _NIFTY, DATA_SOURCE = _build_with_fallback()
DATA_QUALITY = "LIVE" if DATA_SOURCE == "kotak" else "DEMO"
LAST_MARKET_DATA_TS = datetime.now(timezone.utc).isoformat()


def _to_idea(eq: dict) -> dict:
    lv, sc, ind = eq["levels"], eq["scores"], eq["indicators"]
    dir_label = "Bullish" if eq["direction"] == "bullish" else "Bearish"
    reasons, risks = [], []
    if ind["ema20"] and (eq["price"] > ind["ema20"]) == (eq["direction"] == "bullish"):
        reasons.append(f"{'Above' if eq['direction']=='bullish' else 'Below'} 20 EMA")
    if ind["momentum"] and abs(ind["momentum"]) > 1:
        reasons.append("Strong price momentum")
    if ind["volume_ratio"] and ind["volume_ratio"] > 1.2:
        reasons.append("Volume above 20-day average")
    if eq["sector_analysis"]["label"] == "Outperforming":
        reasons.append("Sector outperforming NIFTY")
    if not reasons:
        reasons.append("Multiple research factors aligned")

    if ind["resistance"] and eq["direction"] == "bullish":
        risks.append("Resistance level nearby")
    if _REGIME["regime"] != "BULLISH" and eq["direction"] == "bullish":
        risks.append("Market regime not fully supportive")
    if lv["risk_reward"] < 2:
        risks.append("Risk/Reward below 1:2")
    if not risks:
        risks.append("Standard market risk applies")

    return {
        "id": f"idea-{eq['symbol']}",
        "symbol": eq["symbol"],
        "company": eq["company"],
        "direction": eq["direction"],
        "direction_label": dir_label,
        "idea_type": "Swing",
        "score": sc["overall"],
        "data_quality": eq["data_quality"],
        "data_source": eq["data_source"],
        "entry": lv["entry"],
        "stop_loss": lv["stop_loss"],
        "target1": lv["target1"],
        "target2": lv["target2"],
        "risk": lv["risk"],
        "risk_reward": lv["risk_reward"],
        "rr_flag": eq["opportunity"]["components"]["risk_reward"]["components"]["flag"],
        "reasoning": {
            "technical": f"Technical score {sc['technical']}/35 for a {dir_label.lower()} setup.",
            "fundamental": f"Fundamental score {sc['fundamental']}/25 based on growth, quality and valuation.",
            "sentiment": f"Sentiment score {sc['sentiment']}/15 from recent headlines.",
            "sector": f"Sector strength {sc['sector']}/10 ({eq['sector_analysis']['label']}).",
        },
        "why": reasons,
        "risks": risks,
        "invalidation": (f"Close below stop {lv['stop_loss']}" if eq["direction"] == "bullish"
                         else f"Close above stop {lv['stop_loss']}"),
        "atr": ind["atr"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Research-based opportunity. Not a guaranteed trade. You make the final decision.",
    }


IDEAS = {f"idea-{sym}": _to_idea(eq) for sym, eq in EQUITIES.items()}


def list_equities() -> list[dict]:
    keys = ("symbol", "company", "sector", "price", "change_pct", "volume", "direction",
            "indicators", "scores", "data_source", "is_live", "data_timestamp", "data_quality")
    return [{k: e[k] for k in keys} for e in EQUITIES.values()]


def top_opportunities(n: int = 3) -> list[dict]:
    return sorted(IDEAS.values(), key=lambda i: i["score"], reverse=True)[:n]


def market_overview() -> dict:
    status = mkt.market_status()
    sector_perf = {}
    for s in SECTORS:
        members = [e for e in EQUITIES.values() if e["sector"] == s]
        sector_perf[s] = round(sum(m["change_pct"] for m in members) / len(members), 2)
    changes = [e["change_pct"] for e in EQUITIES.values()]
    advances = sum(1 for c in changes if c > 0)
    return {
        "market_status": status["status"],
        "market_status_detail": status,
        "nifty": {"value": _NIFTY["value"], "change_pct": _NIFTY["change_pct"]},
        "regime": _REGIME,
        "sector_performance": sector_perf,
        "breadth": {"advances": advances, "declines": len(changes) - advances, "total": len(changes)},
        "top_gainers": sorted(list_equities(), key=lambda e: e["change_pct"], reverse=True)[:3],
        "top_losers": sorted(list_equities(), key=lambda e: e["change_pct"])[:3],
        "data_source": DATA_SOURCE,
        "data_quality": DATA_QUALITY,
        "last_market_data_timestamp": LAST_MARKET_DATA_TS,
    }


def current_regime() -> dict:
    return _REGIME


def provider_status() -> dict:
    return {"data_source": DATA_SOURCE, "data_quality": DATA_QUALITY,
            "last_market_data_timestamp": LAST_MARKET_DATA_TS}
