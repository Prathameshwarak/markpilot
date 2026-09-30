"""Provider selection, mock fallback, market status, and websocket lifecycle tests."""
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo


def test_provider_selection_mock_by_default(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "MARKET_DATA_PROVIDER", "mock")
    from providers.factory import get_market_data_provider
    provider, source = get_market_data_provider()
    assert source == "mock"


def test_provider_falls_back_when_kotak_unconfigured(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "MARKET_DATA_PROVIDER", "kotak")
    for k in settings.kotak_required_keys():
        monkeypatch.setattr(settings, k, "")
    from providers.factory import get_market_data_provider
    provider, source = get_market_data_provider()
    assert source == "mock"  # never pretend Kotak when not configured


def test_provider_selects_kotak_when_configured(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "MARKET_DATA_PROVIDER", "kotak")
    monkeypatch.setattr(settings, "KOTAK_CONSUMER_KEY", "ck")
    monkeypatch.setattr(settings, "KOTAK_MOBILE", "+910000000000")
    monkeypatch.setattr(settings, "KOTAK_UCC", "UCC1")
    monkeypatch.setattr(settings, "KOTAK_MPIN", "1234")
    monkeypatch.setattr(settings, "KOTAK_TOTP_SECRET", "JBSWY3DPEHPK3PXP")
    from providers.factory import get_market_data_provider
    provider, source = get_market_data_provider()
    assert source == "kotak"


def test_mock_provider_freshness():
    from providers.mock import MockMarketDataProvider
    q = MockMarketDataProvider().get_quote("RELIANCE")
    assert q["stale"] is False
    assert "price" in q and "change_pct" in q


# ---------- market status ----------
def test_market_status_open():
    import market_status as mkt
    dt = datetime(2026, 6, 30, 11, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Tue 11:00 IST
    assert mkt.market_status(dt)["status"] == "OPEN"


def test_market_status_pre_market():
    import market_status as mkt
    dt = datetime(2026, 6, 30, 9, 5, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert mkt.market_status(dt)["status"] == "PRE_MARKET"


def test_market_status_closed_weekend():
    import market_status as mkt
    dt = datetime(2026, 7, 4, 11, 0, tzinfo=ZoneInfo("Asia/Kolkata"))  # Saturday
    assert mkt.market_status(dt)["status"] == "CLOSED"


def test_market_status_after_hours():
    import market_status as mkt
    dt = datetime(2026, 6, 30, 16, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
    assert mkt.market_status(dt)["status"] == "CLOSED"


# ---------- websocket lifecycle ----------
def test_ws_connect_subscribe_receive():
    from brokers.websocket import MockWebSocketProvider
    ws = MockWebSocketProvider()
    assert ws.connect() is True
    ws.subscribe([{"instrument_token": "2885", "exchange_segment": "nse_cm"}])
    assert len(ws.subscriptions) == 1
    ws.push({"trading_symbol": "RELIANCE-EQ", "last_traded_price": 2900, "volume": 1000})
    ticks = ws.receive()
    assert ticks[0]["symbol"] == "RELIANCE-EQ" and ticks[0]["is_live"] is True


def test_ws_reconnect_capped():
    from brokers.websocket import MockWebSocketProvider
    ws = MockWebSocketProvider(max_reconnects=2)
    ws.connect()
    ws.disconnect()
    assert ws.reconnect() is True
    assert ws.reconnect() is True
    assert ws.reconnect() is False  # capped
    assert ws.reconnect_attempts == 2


def test_ws_subscribe_requires_connection():
    from brokers.websocket import MockWebSocketProvider
    ws = MockWebSocketProvider()
    with pytest.raises(RuntimeError):
        ws.subscribe([{"instrument_token": "1"}])
