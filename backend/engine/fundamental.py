"""Lightweight fundamental scoring (max 25). Never fabricates missing data."""
from __future__ import annotations

UNAVAILABLE = "Data unavailable"


def _pts(value, bands):
    """bands: list of (threshold, points). Higher value = better unless reversed upstream."""
    if value is None:
        return None
    for threshold, points in bands:
        if value >= threshold:
            return points
    return 0


def fundamental_score(m: dict) -> dict:
    """m holds optional keys; None means data unavailable and that component is disabled."""
    comps = {}

    growths = [m.get("revenue_growth"), m.get("profit_growth"), m.get("eps_growth")]
    have = [g for g in growths if g is not None]
    if have:
        avg = sum(have) / len(have)
        comps["growth"] = {"value": round(avg, 2), "points": _pts(avg, [(20, 8), (12, 6), (6, 4), (0, 2)])}
    else:
        comps["growth"] = {"value": UNAVAILABLE, "points": 0}

    roe, roce = m.get("roe"), m.get("roce")
    quality = [x for x in (roe, roce) if x is not None]
    if quality:
        avg = sum(quality) / len(quality)
        comps["quality"] = {"value": round(avg, 2), "points": _pts(avg, [(20, 6), (15, 5), (10, 3), (0, 1)])}
    else:
        comps["quality"] = {"value": UNAVAILABLE, "points": 0}

    de = m.get("debt_equity")
    if de is not None:
        pts = 5 if de <= 0.3 else 4 if de <= 0.7 else 2 if de <= 1.2 else 1
        comps["leverage"] = {"value": de, "points": pts}
    else:
        comps["leverage"] = {"value": UNAVAILABLE, "points": 0}

    pe, pb = m.get("pe"), m.get("pb")
    val_pts = 0
    have_val = False
    if pe is not None:
        have_val = True
        val_pts += 3 if pe <= 25 else 2 if pe <= 40 else 1
    if pb is not None:
        have_val = True
        val_pts += 3 if pb <= 3 else 2 if pb <= 6 else 1
    comps["valuation"] = {"value": {"pe": pe, "pb": pb} if have_val else UNAVAILABLE, "points": val_pts}

    total = sum(c["points"] for c in comps.values())
    return {"score": int(total), "max": 25, "components": comps}
