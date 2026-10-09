import pytest
from engine.monitoring import evaluate, STATES


def test_states_defined():
    assert STATES == ["MONITORING", "T1_HIT", "T2_HIT", "STOP_LOSS_HIT", "INVALIDATED", "CLOSED"]


def test_bullish_t1_detection_moves_stop_to_entry():
    r = evaluate("bullish", entry=100, current_stop=90, target1=110, target2=120,
                 status="MONITORING", price=111, atr_value=2, trail_mult=2)
    assert r["status"] == "T1_HIT"
    assert r["current_stop"] >= 100  # moved to entry (break-even) or trailed higher
    assert any(e["type"] == "T1_HIT" for e in r["events"])


def test_bullish_t2_detection():
    r = evaluate("bullish", 100, 100, 110, 120, "T1_HIT", price=121, atr_value=2)
    assert r["status"] == "T2_HIT"
    assert any(e["type"] == "T2_HIT" for e in r["events"])


def test_bullish_stop_detection():
    r = evaluate("bullish", 100, 95, 110, 120, "MONITORING", price=94, atr_value=2)
    assert r["status"] == "STOP_LOSS_HIT"
    assert any(e["type"] == "STOP_LOSS_HIT" for e in r["events"])


def test_bullish_trailing_stop_after_t1():
    r = evaluate("bullish", 100, 100, 110, 120, "T1_HIT", price=115, atr_value=2, trail_mult=2)
    # trail = 115 - 2*2 = 111 > 100 -> stop moves up
    assert r["current_stop"] == 111
    assert any(e["type"] == "TRAILING_STOP_UPDATED" for e in r["events"])


def test_bearish_t1_detection():
    r = evaluate("bearish", entry=100, current_stop=110, target1=90, target2=80,
                 status="MONITORING", price=89, atr_value=2)
    assert r["status"] == "T1_HIT"
    assert r["current_stop"] <= 100


def test_bearish_stop_detection():
    r = evaluate("bearish", 100, 110, 90, 80, "MONITORING", price=111, atr_value=2)
    assert r["status"] == "STOP_LOSS_HIT"


def test_bearish_trailing_stop_after_t1():
    r = evaluate("bearish", 100, 100, 90, 80, "T1_HIT", price=85, atr_value=2, trail_mult=2)
    # trail = 85 + 4 = 89 < 100 -> stop moves down
    assert r["current_stop"] == 89


def test_terminal_states_are_frozen():
    for terminal in ("STOP_LOSS_HIT", "T2_HIT", "CLOSED", "INVALIDATED"):
        r = evaluate("bullish", 100, 90, 110, 120, terminal, price=105, atr_value=2)
        assert r["status"] == terminal
        assert r["events"] == []


def test_no_event_when_price_between_levels():
    r = evaluate("bullish", 100, 90, 110, 120, "MONITORING", price=105, atr_value=2)
    assert r["status"] == "MONITORING"
    assert r["events"] == []
