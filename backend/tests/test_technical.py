import pytest
from engine import technical as t


def test_ema_constant_series():
    assert t.ema([100] * 30, 20) == pytest.approx(100.0)


def test_rsi_all_gains_is_100():
    assert t.rsi(list(range(1, 40)), 14) == pytest.approx(100.0)


def test_rsi_all_losses_is_low():
    val = t.rsi(list(range(40, 1, -1)), 14)
    assert val is not None and val < 5


def test_rsi_none_when_insufficient():
    assert t.rsi([1, 2, 3], 14) is None


def test_atr_constant_range():
    n = 40
    high = [110] * n
    low = [100] * n
    close = [105] * n
    assert t.atr(high, low, close, 14) == pytest.approx(10.0, abs=0.5)


def test_volume_ratio():
    vols = [100] * 20 + [200]
    assert t.volume_ratio(vols, 20) == pytest.approx(2.0)


def test_price_momentum_positive():
    close = [100 + i for i in range(20)]
    assert t.price_momentum(close, 10) > 0


def test_support_resistance():
    low = [10, 8, 12, 9, 7]
    high = [15, 20, 18, 22, 19]
    s, r = t.support_resistance(low, high, 5)
    assert s == 7 and r == 22


def test_technical_score_bounds():
    ind = {"price": 110, "ema20": 105, "ema50": 100, "rsi": 60, "momentum": 5,
           "volume_ratio": 1.6, "atr": 1.5}
    res = t.technical_score(ind, "bullish")
    assert res["max"] == 35
    assert 0 <= res["score"] <= 35
    assert res["components"]["trend"] == 10  # price>ema20 and ema20>ema50


def test_technical_score_bearish_trend():
    ind = {"price": 90, "ema20": 95, "ema50": 100, "rsi": 35, "momentum": -5,
           "volume_ratio": 1.3, "atr": 1.0}
    res = t.technical_score(ind, "bearish")
    assert res["components"]["trend"] == 10
