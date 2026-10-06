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


# ---------- refreshable build: LIVE / DEMO fallback / PARTIAL ----------
class _LiveClient:
    def __init__(self, *a, fail=(), **k):
        self.fail = set(fail)
    # Official kotakneoapi 3.x shapes: quotes -> list; history -> data.candles.
    def quotes(self, instrument_tokens=None, quote_type=None):
        tok = instrument_tokens[0]["instrument_token"]
        if tok in self.fail:
            return {"status": "ERROR", "fault": {"code": 400, "message": "no quote"}}
        return [{"exchange_token": tok, "ltp": "150.0000", "per_change": "1.3500",
                 "last_volume": "10", "ohlc": {"close": "148.0000"}}]
    def historical_data(self, neosymbol, interval, from_date, to_date):
        return {"status": "success", "data": {"candles": [
            [f"d{i}", 100 + i * .5, 102 + i * .5, 98 + i * .5, 101 + i * .5, 1000 + i, None]
            for i in range(120)]}}


def _kotak_env(monkeypatch, client):
    from config import settings
    from brokers import registry
    from brokers.kotak_neo import KotakNeoAdapter
    monkeypatch.setattr(settings, "MARKET_DATA_PROVIDER", "kotak")
    monkeypatch.setattr(settings, "KOTAK_CONSUMER_KEY", "ck")
    a = KotakNeoAdapter()
    a._client = client
    monkeypatch.setattr(registry, "_adapter", a)
    return a


def test_rebuild_live(monkeypatch):
    import services
    _kotak_env(monkeypatch, _LiveClient())
    st = services.rebuild()
    assert st["data_source"] == "kotak" and st["data_quality"] == "LIVE"
    assert services.EQUITIES["RELIANCE"]["data_source"] == "kotak"
    assert services.EQUITIES["RELIANCE"]["change_pct"] == 1.35
    assert services.market_overview()["data_quality"] == "LIVE"


def test_rebuild_falls_back_to_demo_with_reason(monkeypatch):
    import services

    class Down(_LiveClient):
        def historical_data(self, **k):
            return {"status": "ERROR", "fault": {"code": 503, "message": "Service unavailable"}}

    _kotak_env(monkeypatch, Down())
    st = services.rebuild()
    assert st["data_source"] == "mock" and st["data_quality"] == "DEMO"
    assert "Service unavailable" in st["last_error"] and "NIFTY" in st["last_error"]


def test_rebuild_partial_on_single_symbol_failure(monkeypatch):
    import services
    _kotak_env(monkeypatch, _LiveClient(fail={"2885"}))  # RELIANCE quote fails
    st = services.rebuild()
    assert st["data_source"] == "kotak" and st["data_quality"] == "PARTIAL"
    assert st["failed_symbols"] == ["RELIANCE"]
    assert services.EQUITIES["RELIANCE"]["data_quality"] == "DEMO"
    assert services.EQUITIES["TCS"]["data_quality"] == "LIVE"


def test_test_connection_triggers_rebuild(monkeypatch):
    import asyncio
    import services
    from routes import system
    a = _kotak_env(monkeypatch, _LiveClient())
    monkeypatch.setattr(a, "authenticate", lambda: {"connected": True, "status": "CONNECTED",
                                                    "message": "ok", "timestamp": "t"})
    calls = []
    monkeypatch.setattr(services, "rebuild", lambda: calls.append(1) or {"data_quality": "LIVE"})
    out = asyncio.run(system.kotak_test_connection(user={}))
    assert calls and out["market_data"]["data_quality"] == "LIVE"

    monkeypatch.setattr(a, "authenticate", lambda: {"connected": False, "status": "AUTH_FAILED",
                                                    "message": "x", "timestamp": "t"})
    calls.clear()
    out = asyncio.run(system.kotak_test_connection(user={}))
    assert not calls and out["market_data"] is None


@pytest.fixture(autouse=True)
def _restore_demo_build():
    yield
    import services
    from config import settings
    if settings.MARKET_DATA_PROVIDER == "mock":
        services.rebuild()
