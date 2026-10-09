"""Lexicon sentiment (max 15). SentimentProvider interface lives in providers.base.

FinBERT can be swapped in later behind the same interface without touching scoring.
"""
from __future__ import annotations

POSITIVE = {
    "surge", "beat", "record", "profit", "growth", "upgrade", "gain", "rally",
    "strong", "outperform", "wins", "expansion", "bullish", "buy", "jump", "rises",
    "boost", "high", "robust", "approval", "acquires", "dividend",
}
NEGATIVE = {
    "fall", "miss", "loss", "downgrade", "decline", "weak", "cut", "probe",
    "fraud", "lawsuit", "plunge", "bearish", "sell", "drop", "slump", "warning",
    "resign", "default", "penalty", "recall", "layoff", "delay",
}


def classify(headline: str) -> str:
    words = set(headline.lower().replace(",", " ").replace(".", " ").split())
    pos = len(words & POSITIVE)
    neg = len(words & NEGATIVE)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def sentiment_score(headlines: list[str], direction: str = "bullish") -> dict:
    if not headlines:
        return {"score": 7, "max": 15, "components": {"note": "Data unavailable", "labels": []}}
    labels = [classify(h) for h in headlines]
    pos = labels.count("positive")
    neg = labels.count("negative")
    net = pos - neg  # aligned with bullish
    if direction == "bearish":
        net = -net
    ratio = net / len(labels)  # -1..1
    score = round((ratio + 1) / 2 * 15)  # map to 0..15
    score = max(0, min(15, score))
    return {
        "score": int(score),
        "max": 15,
        "components": {"positive": pos, "neutral": labels.count("neutral"), "negative": neg, "labels": labels},
    }
