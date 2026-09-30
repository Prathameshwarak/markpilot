"""Research service: composes providers + engine into equities, research snapshots,
trade ideas and market overview. Deterministic and cached at import.
"""
from __future__ import annotations
from datetime import datetime, timezone

from providers.mock import (
    MockMarketDataProvider, MockFundamentalDataProvider, MockNewsProvider, LexiconSentimentProvider,
)
from data.universe import UNIVERSE, SECTORS
from engine import technical, fundamental, sector as sector_engine, risk, scoring

_market = MockMarketDataProvider()
_fund = MockFundamentalDataProvider()
_news = MockNewsProvider()
_sentiment = LexiconSentimentProvider()

_NIFTY = _market.get_index("NIFTY")
_REGIME = scoring.market_regime(_NIFTY["close"])


def _sector_return(candles: dict) -> float:
    c = candles["close"]
    return (c[-1] / c[-21] - 1) * 100 if len(c) >= 21 else 0.0


def _build_one(symbol: str) -> dict:
    meta = UNIVERSE[symbol]
    candles = _market.get_historical(symbol)
    ind = technical.analyze(candles)
    direction = "bullish" if (ind["ema20"] and ind["price"] > ind["ema20"]) else "bearish"

    stock_ret = _sector_return(candles)
    nifty_ret = (_NIFTY["close"][-1] / _NIFTY["close"][-21] - 1) * 100
    sector_ret = stock_ret * 0.85 + nifty_ret * 0.15  # mock proxy for sector index

    tech = technical.technical_score(ind, direction)
    fund = fundamental.fundamental_score(_fund.get_fundamentals(symbol))
    news = _news.get_news(symbol)
    sent = _sentiment.score([n["headline"] for n in news], direction)
    sect = sector_engine.sector_score(stock_ret, sector_ret, nifty_ret, direction)

    levels = risk.compute_levels(ind["price"], ind["atr"] or ind["price"] * 0.02, direction)
    rr = risk.risk_reward_score(levels["risk_reward"])
    opp = scoring.opportunity_score(tech, fund, sent, sect, rr)

    return {
        "symbol": symbol,
        "company": meta["name"],
        "sector": meta["sector"],
        "price": ind["price"],
        "change_pct": _market.get_quote(symbol)["change_pct"],
        "volume": candles["volume"][-1],
        "direction": direction,
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


# Build once (deterministic).
EQUITIES = {sym: _build_one(sym) for sym in UNIVERSE}


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
    keys = ("symbol", "company", "sector", "price", "change_pct", "volume", "direction", "indicators", "scores")
    return [{k: e[k] for k in keys} for e in EQUITIES.values()]


def top_opportunities(n: int = 3) -> list[dict]:
    ideas = sorted(IDEAS.values(), key=lambda i: i["score"], reverse=True)
    return ideas[:n]


def market_overview() -> dict:
    sector_perf = {}
    for s in SECTORS:
        members = [e for e in EQUITIES.values() if e["sector"] == s]
        sector_perf[s] = round(sum(m["change_pct"] for m in members) / len(members), 2)
    changes = [e["change_pct"] for e in EQUITIES.values()]
    advances = sum(1 for c in changes if c > 0)
    return {
        "market_status": "OPEN",
        "nifty": {"value": _NIFTY["value"], "change_pct": _NIFTY["change_pct"]},
        "regime": _REGIME,
        "sector_performance": sector_perf,
        "breadth": {"advances": advances, "declines": len(changes) - advances, "total": len(changes)},
        "top_gainers": sorted(list_equities(), key=lambda e: e["change_pct"], reverse=True)[:3],
        "top_losers": sorted(list_equities(), key=lambda e: e["change_pct"])[:3],
        "data_source": "mock",
    }


def current_regime() -> dict:
    return _REGIME
