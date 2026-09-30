import pytest
from engine import risk


def test_bullish_levels():
    lv = risk.compute_levels(100, 5, "bullish", stop_mult=2, t1_r=1, t2_r=2)
    assert lv["stop_loss"] == 90
    assert lv["risk"] == 10
    assert lv["target1"] == 110
    assert lv["target2"] == 120
    assert lv["risk_reward"] == 2.0


def test_bearish_levels():
    lv = risk.compute_levels(100, 5, "bearish", stop_mult=2, t1_r=1, t2_r=2)
    assert lv["stop_loss"] == 110
    assert lv["risk"] == 10
    assert lv["target1"] == 90
    assert lv["target2"] == 80
    assert lv["risk_reward"] == 2.0


def test_rr_flags():
    assert risk.risk_reward_score(3.0)["components"]["flag"] == "Strong R:R"
    assert risk.risk_reward_score(2.0)["components"]["flag"] == "Acceptable R:R"
    assert risk.risk_reward_score(1.0)["components"]["flag"] == "Low R:R"


def test_rr_score_bounds():
    for rr in (0.5, 1.5, 2.0, 3.5):
        res = risk.risk_reward_score(rr)
        assert 0 <= res["score"] <= 15
