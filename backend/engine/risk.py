"""Deterministic entry / stop / target / risk-reward logic. Rules are configurable."""
from __future__ import annotations
from config import settings


def compute_levels(entry: float, atr_value: float, direction: str = "bullish",
                   stop_mult: float | None = None, t1_r: float | None = None, t2_r: float | None = None) -> dict:
    stop_mult = settings.ATR_STOP_MULTIPLIER if stop_mult is None else stop_mult
    t1_r = settings.TARGET1_R if t1_r is None else t1_r
    t2_r = settings.TARGET2_R if t2_r is None else t2_r

    if direction == "bullish":
        stop = entry - stop_mult * atr_value
        risk = entry - stop
        t1 = entry + t1_r * risk
        t2 = entry + t2_r * risk
    else:
        stop = entry + stop_mult * atr_value
        risk = stop - entry
        t1 = entry - t1_r * risk
        t2 = entry - t2_r * risk

    reward_t1 = abs(t1 - entry)
    reward_t2 = abs(t2 - entry)
    rr = round(reward_t2 / risk, 2) if risk else 0
    return {
        "entry": round(entry, 2),
        "stop_loss": round(stop, 2),
        "target1": round(t1, 2),
        "target2": round(t2, 2),
        "risk": round(risk, 2),
        "reward_t1": round(reward_t1, 2),
        "reward_t2": round(reward_t2, 2),
        "risk_reward": rr,
    }


def risk_reward_score(rr: float) -> dict:
    if rr >= 3:
        score, flag = 15, "Strong R:R"
    elif rr >= 2:
        score, flag = 12, "Acceptable R:R"
    elif rr >= 1.5:
        score, flag = 8, "Acceptable R:R"
    else:
        score, flag = 4, "Low R:R"
    return {"score": score, "max": 15, "components": {"risk_reward": rr, "flag": flag}}
