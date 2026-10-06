"""Kotak adapter + market-data provider tests. NO real credentials required — the SDK
client is faked and env vars are monkeypatched.
"""
import pytest
from datetime import datetime, timezone

from brokers.kotak_neo import KotakNeoAdapter, READ_ONLY_METHODS
from brokers import instruments


# ---------- instrument mapping ----------
def test_get_instrument_known():
    inst = instruments.get_instrument("RELIANCE")
    assert inst is not None
    assert inst.exchange == "nse_cm"
    assert inst.trading_symbol == "RELIANCE-EQ"
    assert inst.broker_instrument_token is not None


def test_get_instrument_unknown():
    assert instruments.get_instrument("NOPE") is None


def test_adapter_is_read_only():
    # Order-mutating methods must never be part of the adapter's public surface.
    a = KotakNeoAdapter()
    for forbidden in ("place_order", "modify_order", "cancel_order"):
        assert not hasattr(a, forbidden)
    assert "place_order" not in READ_ONLY_METHODS


# ---------- configuration / missing creds ----------
def test_not_configured_authenticate(monkeypatch):
    from config import settings
    for k in settings.kotak_required_keys():
        monkeypatch.setattr(settings, k, "")
    a = KotakNeoAdapter()
    res = a.authenticate()
    assert res["connected"] is False
    assert res["status"] == "NOT_CONFIGURED"
    assert "token" not in res and "mpin" not in str(res).lower()


def test_health_check_no_secret_leak():
    a = KotakNeoAdapter()
    h = a.health_check()
    assert h["order_execution"] == "disabled"
    assert h["broker"] == "kotak_neo"
    blob = str(h).lower()
    for leak in ("mpin", "totp_secret", "consumer_key"):
        assert leak not in blob or h.get(leak) is None


# ---------- successful mocked authentication ----------
class _FakeClient:
    def __init__(self, *a, **k):
        self.logged_in = False
    def totp_login(self, **k):
        return {"data": "ok"}
    def totp_validate(self, **k):
        self.logged_in = True
        return {"data": {"baseUrl": "https://x"}}
    # Shapes below follow the official kotakneoapi 3.x docs (quotes.md / historical_data.md).
    def quotes(self, instrument_tokens=None, quote_type=None):
        return [{
            "exchange_token": "2885", "display_symbol": "RELIANCE-EQ", "exchange": "nse_cm",
            "lstup_time": "1782374657", "ltp": "2905.5000", "last_volume": "1234567",
            "change": "10.5000", "per_change": "0.3600",
            "ohlc": {"open": "2890.0000", "high": "2920.0000", "low": "2880.0000", "close": "2895.0000"},
        }]
    def historical_data(self, **k):
        base = 100
        return {"status": "success", "interval": "D", "data": {"candles": [
            [f"2026-01-{(i%28)+1:02d}T00:00:00+0530", base + i, base + i + 2,
             base + i - 2, base + i + 1, 1000 + i, None] for i in range(120)]}}


def _configure(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "KOTAK_CONSUMER_KEY", "ck")
    monkeypatch.setattr(settings, "KOTAK_MOBILE", "+910000000000")
    monkeypatch.setattr(settings, "KOTAK_UCC", "UCC1")
    monkeypatch.setattr(settings, "KOTAK_MPIN", "1234")
    monkeypatch.setattr(settings, "KOTAK_TOTP_SECRET", "JBSWY3DPEHPK3PXP")


def test_successful_mocked_auth_and_quote(monkeypatch):
    _configure(monkeypatch)
    a = KotakNeoAdapter()
    # Inject a connected fake client directly (bypass network).
    a._client = _FakeClient()
    a._connected = True
    a._status = "CONNECTED"
    q = a.get_quote("RELIANCE")
    assert q["symbol"] == "RELIANCE"
    assert q["ltp"] == 2905.5
    assert q["source"] == "kotak" and q["is_live"] is True
    assert q["change_pct"] == 0.36 and q["close"] == 2895.0 and q["volume"] == 1234567.0


def test_quote_normalization_missing_prevclose(monkeypatch):
    a = KotakNeoAdapter()
    inst = instruments.get_instrument("TCS")
    out = a._normalize_quote([{"exchange_token": "11536", "ltp": "100"}], inst)
    assert out["ltp"] == 100
    assert out["change_pct"] is None  # cannot compute without prev close / per_change


def test_historical_normalization(monkeypatch):
    a = KotakNeoAdapter()
    candles = a._normalize_candles(_FakeClient().historical_data())
    assert len(candles) == 120
    assert set(candles[0].keys()) == {"timestamp", "open", "high", "low", "close", "volume"}


def test_get_quote_requires_session():
    a = KotakNeoAdapter()
    with pytest.raises(RuntimeError):
        a.get_quote("RELIANCE")


def test_invalid_broker_response():
    a = KotakNeoAdapter()
    inst = instruments.get_instrument("INFY")
    from brokers.kotak_neo import KotakAPIError
    with pytest.raises(KotakAPIError):  # malformed -> clear failure, never fake values
        a._normalize_quote({"garbage": True}, inst)


# ---------- provider layer ----------
def test_kotak_provider_quote_and_history(monkeypatch):
    import cache
    cache.clear()
    from providers.kotak_provider import KotakMarketDataProvider
    a = KotakNeoAdapter()
    a._client = _FakeClient()
    a._connected = True
    a._status = "CONNECTED"
    p = KotakMarketDataProvider(a)
    q = p.get_quote("RELIANCE")
    assert q["source"] == "kotak" and q["is_live"] is True and q["stale"] is False
    hist = p.get_historical("RELIANCE")
    assert len(hist["close"]) == 120


def test_kotak_provider_insufficient_data(monkeypatch):
    import cache
    cache.clear()
    from providers.kotak_provider import KotakMarketDataProvider

    class ShortClient(_FakeClient):
        def historical_data(self, **k):
            return {"status": "success", "data": {"candles": [[f"d{i}", 1, 1, 1, 1, 1, None] for i in range(10)]}}

    a = KotakNeoAdapter()
    a._client = ShortClient()
    a._connected = True
    p = KotakMarketDataProvider(a)
    with pytest.raises(RuntimeError):
        p.get_historical("RELIANCE")


# ---------- live-data fix: index path, SDK args, error payloads, read-only ----------
from datetime import date as _date


class _RecordingClient(_FakeClient):
    def __init__(self, *a, **k):
        super().__init__()
        self.hist_calls = []

    def historical_data(self, neosymbol, interval, from_date, to_date):  # exact SDK 3.x signature
        self.hist_calls.append(dict(neosymbol=neosymbol, interval=interval,
                                    from_date=from_date, to_date=to_date))
        return _FakeClient.historical_data(self)


def test_neosymbol_index_and_stock():
    assert instruments.neosymbol("NIFTY") == "nse_cm|Nifty 50"
    assert instruments.neosymbol_candidates("NIFTY") == ["nse_cm|Nifty 50", "nse_cm|26000"]
    assert instruments.neosymbol("RELIANCE") == "nse_cm|2885"
    assert instruments.neosymbol("NOPE") is None


def test_historical_data_uses_sdk_signature():
    a = KotakNeoAdapter()
    a._client = _RecordingClient()
    a.get_historical_data("RELIANCE", interval="day", days=120)
    call = a._client.hist_calls[0]
    assert call["neosymbol"] == "nse_cm|2885" and call["interval"] == "D"
    f, t = _date.fromisoformat(call["from_date"]), _date.fromisoformat(call["to_date"])
    assert t == _date.today() and 100 <= (t - f).days <= 170


def test_nifty_uses_index_token_path():
    import cache
    cache.clear()
    from providers.kotak_provider import KotakMarketDataProvider
    a = KotakNeoAdapter()
    a._client = _RecordingClient()
    idx = KotakMarketDataProvider(a).get_index("NIFTY")
    assert a._client.hist_calls[0]["neosymbol"] == "nse_cm|Nifty 50"
    assert idx["source"] == "kotak" and len(idx["close"]) == 120


@pytest.mark.parametrize("payload", [
    {"error": [{"code": "401", "message": "Invalid consumer key"}]},
    {"Error": "Unexpected response format", "Exception": "x", "StatusCode": 502},
    {"stat": "Not_Ok", "emsg": "Session expired"},
    {"status": "ERROR", "fault": {"code": 400, "message": "Invalid interval value"}},
])
def test_sdk_error_payloads_are_failures(payload):
    from brokers.kotak_neo import KotakAPIError

    class ErrClient(_FakeClient):
        def quotes(self, **k): return payload
        def historical_data(self, **k): return payload

    a = KotakNeoAdapter()
    a._client = ErrClient()
    with pytest.raises(KotakAPIError):
        a.get_quote("RELIANCE")
    with pytest.raises(KotakAPIError):
        a.get_historical_data("NIFTY")
    assert a.health_check()["last_error"]


def test_authenticate_rejects_error_payload(monkeypatch):
    _configure(monkeypatch)
    import neo_api_client

    class BadLogin(_FakeClient):
        def totp_login(self, **k):
            return {"error": [{"code": "400", "message": "Invalid TOTP"}]}

    monkeypatch.setattr(neo_api_client, "NeoAPI", BadLogin)
    a = KotakNeoAdapter()
    res = a.authenticate()
    assert res["connected"] is False and res["status"] == "AUTH_FAILED"


def test_authenticate_success(monkeypatch):
    _configure(monkeypatch)
    import neo_api_client
    monkeypatch.setattr(neo_api_client, "NeoAPI", _FakeClient)
    res = KotakNeoAdapter().authenticate()
    assert res["connected"] is True and res["status"] == "CONNECTED"


def test_market_data_without_totp_session(monkeypatch):
    from config import settings
    import neo_api_client
    monkeypatch.setattr(settings, "KOTAK_CONSUMER_KEY", "ck")
    monkeypatch.setattr(settings, "KOTAK_MPIN", "")  # no TOTP/MPIN session possible
    monkeypatch.setattr(neo_api_client, "NeoAPI", _FakeClient)
    a = KotakNeoAdapter()
    assert a.get_quote("RELIANCE")["ltp"] == 2905.5


def test_no_order_methods_on_adapter():
    for m in ("place_order", "modify_order", "cancel_order"):
        assert not hasattr(KotakNeoAdapter, m)
        assert m not in READ_ONLY_METHODS


def test_secrets_never_logged(monkeypatch, caplog):
    _configure(monkeypatch)
    from config import settings
    import neo_api_client

    class Leaky(_FakeClient):
        def totp_validate(self, **k):
            return {"error": [{"message": f"bad mpin {settings.KOTAK_MPIN} key {settings.KOTAK_CONSUMER_KEY}x"}]}

    monkeypatch.setattr(neo_api_client, "NeoAPI", Leaky)
    monkeypatch.setattr(settings, "KOTAK_MPIN", "987654")
    monkeypatch.setattr(settings, "KOTAK_CONSUMER_KEY", "SECRETKEY123")
    import logging
    caplog.set_level(logging.DEBUG)
    a = KotakNeoAdapter()
    a.authenticate()
    blob = caplog.text + str(a.health_check())
    assert "987654" not in blob and "SECRETKEY123" not in blob


# ---------- follow-up: real response shapes, 180-day limit, NIFTY fallback ----------
@pytest.fixture(autouse=True)
def _reset_index_resolution():
    instruments._INDEX_RESOLVED.clear()
    yield
    instruments._INDEX_RESOLVED.clear()


def test_candles_parsed_from_data_candles():
    out = KotakNeoAdapter._normalize_candles(
        {"status": "success", "data": {"candles": [["2026-08-20T09:15:00+0530", 1, 2, 0.5, 1.5, 100, None]]}})
    assert out == [{"timestamp": "2026-08-20T09:15:00+0530", "open": 1.0, "high": 2.0,
                    "low": 0.5, "close": 1.5, "volume": 100.0}]


@pytest.mark.parametrize("payload", [{"status": "success", "data": {"candles": []}},
                                     {"status": "success", "data": {}}, {"status": "success"}, {}])
def test_empty_or_malformed_history_is_failure(payload):
    from brokers.kotak_neo import KotakAPIError

    class C(_FakeClient):
        def historical_data(self, **k): return payload

    a = KotakNeoAdapter()
    a._client = C()
    with pytest.raises(KotakAPIError):
        a.get_historical_data("RELIANCE")


@pytest.mark.parametrize("payload", [[], [{}], [{"ltp": ""}], [{"ltp": "0"}], {"data": "x"}, "junk"])
def test_empty_or_malformed_quote_is_failure(payload):
    from brokers.kotak_neo import KotakAPIError

    class C(_FakeClient):
        def quotes(self, **k): return payload

    a = KotakNeoAdapter()
    a._client = C()
    with pytest.raises(KotakAPIError):
        a.get_quote("RELIANCE")


@pytest.mark.parametrize("days,start,end", [(120, None, None), (500, None, None), (1, None, None),
                                            (120, "2025-01-01", "2026-06-30")])
def test_history_window_never_exceeds_limit(days, start, end):
    from brokers.kotak_neo import history_window, MAX_HISTORY_SPAN_DAYS
    f, t = history_window(days, start, end)
    assert f is not None and t is not None and f < t
    assert (t - f).days <= MAX_HISTORY_SPAN_DAYS < 180


def test_nifty_falls_back_to_numeric_token_and_remembers():
    class C(_RecordingClient):
        def historical_data(self, neosymbol, interval, from_date, to_date):
            self.hist_calls.append(dict(neosymbol=neosymbol))
            if neosymbol == "nse_cm|Nifty 50":
                return {"status": "ERROR", "fault": {"code": 400, "message": "Invalid neosymbol"}}
            return _FakeClient.historical_data(self)

    a = KotakNeoAdapter()
    a._client = C()
    assert len(a.get_historical_data("NIFTY")) == 120
    assert [c["neosymbol"] for c in a._client.hist_calls] == ["nse_cm|Nifty 50", "nse_cm|26000"]
    assert instruments.neosymbol("NIFTY") == "nse_cm|26000"


def test_nifty_all_identifiers_fail_reports_fault_message():
    from brokers.kotak_neo import KotakAPIError

    class C(_FakeClient):
        def historical_data(self, **k):
            return {"status": "ERROR", "fault": {"code": 400, "message": "Invalid neosymbol"}}

    a = KotakNeoAdapter()
    a._client = C()
    with pytest.raises(KotakAPIError) as ei:
        a.get_historical_data("NIFTY")
    assert "Invalid neosymbol" in str(ei.value) and "Invalid neosymbol" in a.health_check()["last_error"]


def test_validate_market_data_sanitized(monkeypatch):
    from config import settings
    monkeypatch.setattr(settings, "KOTAK_CONSUMER_KEY", "SECRETKEY123")
    a = KotakNeoAdapter()
    a._client = _FakeClient()
    out = a.validate_market_data()
    assert out["nifty_history"] and out["nifty_neosymbol"] == "nse_cm|Nifty 50" and out["quote"]
    assert "SECRETKEY123" not in str(out)
