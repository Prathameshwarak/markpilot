"""Deterministic monitoring state machine + trailing stop. No orders are ever placed."""
from __future__ import annotations
from datetime import datetime, timezone

STATES = ["MONITORING", "T1_HIT", "T2_HIT", "STOP_LOSS_HIT", "INVALIDATED", "CLOSED"]


def _event(event_type: str, message: str, **extra) -> dict:
    return {"type": event_type, "message": message, "timestamp": datetime.now(timezone.utc).isoformat(), **extra}


def evaluate(direction: str, entry: float, current_stop: float, target1: float, target2: float,
             status: str, price: float, atr_value: float, trail_mult: float = 2.0) -> dict:
    """Pure evaluation. Returns new status, new stop, and any events generated."""
    events: list[dict] = []
    new_status = status
    new_stop = current_stop

    if status in ("STOP_LOSS_HIT", "T2_HIT", "INVALIDATED", "CLOSED"):
        return {"status": status, "current_stop": current_stop, "events": events}

    bullish = direction == "bullish"
    stop_hit = price <= current_stop if bullish else price >= current_stop
    t2_hit = price >= target2 if bullish else price <= target2
    t1_hit = price >= target1 if bullish else price <= target1

    if stop_hit:
        new_status = "STOP_LOSS_HIT"
        events.append(_event("STOP_LOSS_HIT", f"Price {price} hit stop {current_stop}", price=price))
        return {"status": new_status, "current_stop": new_stop, "events": events}

    if t2_hit:
        new_status = "T2_HIT"
        events.append(_event("T2_HIT", f"Price {price} reached Target 2 {target2}", price=price))
    elif t1_hit:
        if status == "MONITORING":
            new_status = "T1_HIT"
            events.append(_event("T1_HIT", f"Price {price} reached Target 1 {target1}", price=price))
            # Move stop to entry (break-even) once T1 is achieved.
            moved = max(current_stop, entry) if bullish else min(current_stop, entry)
            if moved != current_stop:
                new_stop = moved
                events.append(_event("TRAILING_STOP_UPDATED", f"Stop moved to break-even {new_stop}",
                                     old_stop=current_stop, new_stop=new_stop, reason="T1 reached"))
        # ATR trailing after T1.
        trail = price - trail_mult * atr_value if bullish else price + trail_mult * atr_value
        better = trail > new_stop if bullish else trail < new_stop
        if better:
            events.append(_event("TRAILING_STOP_UPDATED", f"Trailing stop to {round(trail, 2)}",
                                 old_stop=new_stop, new_stop=round(trail, 2), reason="ATR trail"))
            new_stop = round(trail, 2)

    return {"status": new_status, "current_stop": new_stop, "events": events}
