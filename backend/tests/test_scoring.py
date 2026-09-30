import pytest
from engine import fundamental, sentiment, sector, scoring


def test_fundamental_max_bounds():
    m = {"revenue_growth": 25, "profit_growth": 25, "eps_growth": 25, "roe": 30, "roce": 30,
         "debt_equity": 0.1, "pe": 20, "pb": 2}
    res = fundamental.fundamental_score(m)
    assert res["max"] == 25
    assert res["score"] <= 25


def test_fundamental_missing_data_disabled():
    m = {"revenue_growth": None, "profit_growth": None, "eps_growth": None,
         "roe": None, "roce": None, "debt_equity": None, "pe": None, "pb": None}
    res = fundamental.fundamental_score(m)
    assert res["score"] == 0
    assert res["components"]["growth"]["value"] == fundamental.UNAVAILABLE


def test_sentiment_positive():
    heads = ["Company reports record profit and strong growth",
             "Company shares rally on upgrade"]
    res = sentiment.sentiment_score(heads, "bullish")
    assert res["score"] > 7 and res["max"] == 15


def test_sentiment_negative():
    heads = ["Company faces fraud probe", "Company profit plunge, downgrade"]
    res = sentiment.sentiment_score(heads, "bullish")
    assert res["score"] < 7


def test_sentiment_empty_data_unavailable():
    res = sentiment.sentiment_score([], "bullish")
    assert res["components"]["note"] == "Data unavailable"


def test_sector_outperforming():
    res = sector.sector_score(5.0, 3.0, 1.0, "bullish")
    assert res["components"]["label"] == "Outperforming"
    assert 0 <= res["score"] <= 10


def test_opportunity_score_sums_to_total():
    tech = {"score": 30, "max": 35}
    fund = {"score": 20, "max": 25}
    sent = {"score": 11, "max": 15}
    sect = {"score": 8, "max": 10}
    rr = {"score": 14, "max": 15}
    res = scoring.opportunity_score(tech, fund, sent, sect, rr)
    assert res["total"] == 83
    assert res["max"] == 100
    assert res["breakdown"]["technical"]["score"] == 30


def test_market_regime_bullish():
    close = [100 + i * 0.5 for i in range(60)]
    res = scoring.market_regime(close)
    assert res["regime"] in ("BULLISH", "NEUTRAL", "BEARISH")
    assert res["regime"] == "BULLISH"
