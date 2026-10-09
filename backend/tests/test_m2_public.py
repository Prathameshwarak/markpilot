"""Milestone 2 e2e tests against public preview URL.

Covers:
- /api/system/status expanded fields
- /api/broker/kotak/status auth + shape + no secrets
- /api/broker/kotak/test-connection auth + shape + no secrets
- equities response carries data_source/data_quality/is_live
- overview market_status field
- no Kotak credential values leak in any response
"""
import os
import json
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://marketpilot-equity.preview.emergentagent.com").rstrip("/")
DEMO_EMAIL = "demo@marketpilot.in"
DEMO_PASSWORD = "Demo1234!"

# Kotak-related keys / values that must never leak
FORBIDDEN_KEYS = {
    "KOTAK_CONSUMER_KEY", "KOTAK_CONSUMER_SECRET", "KOTAK_API_KEY", "KOTAK_API_SECRET",
    "KOTAK_MPIN", "KOTAK_TOTP_SECRET", "KOTAK_MOBILE", "KOTAK_UCC",
    "consumer_key", "consumer_secret", "api_key", "api_secret", "mpin", "totp_secret",
    "access_token", "session_token", "auth_token", "sid", "hs_server_id",
}


def _flatten(o, out=None):
    if out is None:
        out = []
    if isinstance(o, dict):
        for k, v in o.items():
            out.append(("key", str(k)))
            _flatten(v, out)
    elif isinstance(o, list):
        for v in o:
            _flatten(v, out)
    else:
        out.append(("val", str(o) if o is not None else ""))
    return out


def _assert_no_secret_leak(payload):
    flat = _flatten(payload)
    keys = {v for t, v in flat if t == "key"}
    # keys such as required_env may list env NAMES — that's fine. What we must not see is a *value*
    # associated with a secret. Check that any key like KOTAK_* or consumer_* etc. doesn't map to a value.
    def walk(o, parent_key=None):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in FORBIDDEN_KEYS and not isinstance(v, (list, dict)):
                    # allowed if value is empty/None
                    assert v in (None, "", False), f"Secret-like key '{k}' leaked value: {v!r}"
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, parent_key)
    walk(payload)


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    token = r.json().get("access_token") or r.json().get("token")
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# ---------- system status ----------

def test_system_status_expanded_fields():
    r = requests.get(f"{BASE_URL}/api/system/status", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("application") == "HEALTHY"
    assert d.get("database") == "CONNECTED"
    assert d.get("market_data") == "MOCK"
    assert d.get("data_source") == "mock"
    assert d.get("data_quality") == "DEMO"
    assert d.get("kotak") == "NOT_CONFIGURED"
    assert d.get("scheduler") == "READY"
    assert "last_market_data_timestamp" in d
    assert d["last_market_data_timestamp"]
    assert d.get("broker", {}).get("order_execution") == "disabled"
    assert d.get("modules", {}).get("fno") == "coming_soon"
    _assert_no_secret_leak(d)


# ---------- kotak status ----------

def test_kotak_status_requires_auth():
    r = requests.get(f"{BASE_URL}/api/broker/kotak/status", timeout=15)
    assert r.status_code in (401, 403)


def test_kotak_status_auth_shape(session):
    r = session.get(f"{BASE_URL}/api/broker/kotak/status", timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("status") == "NOT_CONFIGURED"
    assert d.get("order_execution") == "disabled"
    assert "required_env" in d and isinstance(d["required_env"], list) and len(d["required_env"]) > 0
    _assert_no_secret_leak(d)


# ---------- kotak test-connection ----------

def test_kotak_test_connection_requires_auth():
    r = requests.post(f"{BASE_URL}/api/broker/kotak/test-connection", timeout=15)
    assert r.status_code in (401, 403)


def test_kotak_test_connection_shape(session):
    r = session.post(f"{BASE_URL}/api/broker/kotak/test-connection", timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    assert set(d.keys()) == {"connected", "status", "message", "timestamp"}, f"unexpected keys: {d.keys()}"
    assert d["connected"] is False
    assert d["status"] == "NOT_CONFIGURED"
    assert isinstance(d["message"], str)
    assert isinstance(d["timestamp"], str)
    _assert_no_secret_leak(d)


# ---------- equities data flags ----------

def test_equities_have_data_source_flags():
    r = requests.get(f"{BASE_URL}/api/equities", timeout=20)
    assert r.status_code == 200, r.text
    payload = r.json()
    rows = payload["equities"] if isinstance(payload, dict) else payload
    assert isinstance(rows, list) and len(rows) >= 12
    for row in rows[:5]:
        assert row.get("data_source") == "mock", row
        assert row.get("data_quality") == "DEMO", row
        assert row.get("is_live") is False, row


# ---------- market overview ----------

def test_overview_has_market_status():
    r = requests.get(f"{BASE_URL}/api/market/overview", timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    ms = d.get("market_status")
    assert ms in ("OPEN", "PRE_MARKET", "CLOSED"), f"unexpected market_status={ms!r}"


# ---------- global secret sweep ----------

def test_no_kotak_secrets_in_any_response(session):
    # System status is public, broker endpoints need auth
    for method, path, use_auth in [
        ("GET",  "/api/system/status", False),
        ("GET",  "/api/broker/kotak/status", True),
        ("POST", "/api/broker/kotak/test-connection", True),
        ("GET",  "/api/equities", False),
        ("GET",  "/api/market/overview", False),
    ]:
        s = session if use_auth else requests
        r = s.request(method, f"{BASE_URL}{path}", timeout=20)
        assert r.status_code == 200, f"{path} -> {r.status_code}"
        _assert_no_secret_leak(r.json())
