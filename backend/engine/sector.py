"""Sector-relative strength (max 10)."""
from __future__ import annotations


def sector_score(stock_return: float, sector_return: float, nifty_return: float, direction: str = "bullish") -> dict:
    vs_sector = stock_return - sector_return
    vs_nifty = sector_return - nifty_return
    if direction == "bearish":
        vs_sector, vs_nifty = -vs_sector, -vs_nifty

    score = 5  # neutral baseline
    score += 3 if vs_sector > 0 else -2
    score += 2 if vs_nifty > 0 else -1
    score = max(0, min(10, score))

    if vs_sector > 0 and vs_nifty > 0:
        label = "Outperforming"
    elif vs_sector < 0 and vs_nifty < 0:
        label = "Underperforming"
    else:
        label = "Neutral"

    return {
        "score": int(score),
        "max": 10,
        "components": {"stock_vs_sector": round(vs_sector, 2), "sector_vs_nifty": round(vs_nifty, 2), "label": label},
    }
