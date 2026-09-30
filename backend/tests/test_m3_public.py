"""M3 public tests — Telegram notification preferences + security (token never exposed)."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
DEMO_EMAIL = "demo@marketpilot.in"
DEMO_PASSWORD = "Demo1234!"

FORBIDDEN_TOKEN_KEYS = {"telegram_bot_token", "TELEGRAM_BOT_TOKEN", "bot_token"}


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD}, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    if tok:
        s.headers.update({"Authorization": f"Bearer {tok}"})
    return s


# ---------- auth guards ----------

def test_get_notifications_requires_auth():
    r = requests.get(f"{BASE_URL}/api/notifications/settings", timeout=15)
    assert r.status_code == 401


def test_put_notifications_requires_auth():
    r = requests.put(f"{BASE_URL}/api/notifications/settings", json={}, timeout=15)
    assert r.status_code == 401


def test_test_telegram_requires_auth():
    r = requests.post(f"{BASE_URL}/api/notifications/telegram/test", json={}, timeout=15)
    assert r.status_code == 401


# ---------- GET settings ----------

def test_get_notifications_shape(session):
    r = session.get(f"{BASE_URL}/api/notifications/settings", timeout=15)
    assert r.status_code == 200
    data = r.json()
    for k in ["telegram_enabled", "telegram_chat_id", "alert_entry", "alert_stop",
              "alert_target", "alert_trailing", "alert_regime", "daily_summary",
              "telegram_bot_configured"]:
        assert k in data, f"missing key {k}"
    assert isinstance(data["telegram_bot_configured"], bool)
    # No token leakage
    for k in FORBIDDEN_TOKEN_KEYS:
        assert k not in data
    # Since env has no TELEGRAM_BOT_TOKEN
    assert data["telegram_bot_configured"] is False


# ---------- PUT settings persistence ----------

def test_put_notifications_persist(session):
    payload = {
        "telegram_enabled": True,
        "telegram_chat_id": "123456789",
        "alert_entry": False,
        "alert_stop": True,
        "alert_target": False,
        "alert_trailing": True,
        "alert_regime": False,
        "daily_summary": True,
    }
    r = session.put(f"{BASE_URL}/api/notifications/settings", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    for k, v in payload.items():
        assert body[k] == v
    # No secrets leaked
    for k in FORBIDDEN_TOKEN_KEYS:
        assert k not in body

    # Re-GET verifies persistence
    r2 = session.get(f"{BASE_URL}/api/notifications/settings", timeout=15)
    assert r2.status_code == 200
    got = r2.json()
    for k, v in payload.items():
        assert got[k] == v, f"{k} did not persist: got {got[k]}"


# ---------- Telegram test (no token configured) ----------

def test_telegram_test_not_configured(session):
    r = session.post(f"{BASE_URL}/api/notifications/telegram/test",
                     json={"telegram_chat_id": "123456789"}, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("sent") is False
    assert body.get("configured") is False
    assert "not configured" in (body.get("message") or "").lower()
    for k in FORBIDDEN_TOKEN_KEYS:
        assert k not in body


# ---------- Global security sweep across sensitive endpoints ----------

TOKEN_VALUE_PATTERNS = [
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_-]{30,}\b"),  # Telegram bot token pattern
]


def _no_token_leak(text: str):
    for pat in TOKEN_VALUE_PATTERNS:
        assert not pat.search(text), f"Token-like pattern detected: {pat.pattern}"
    low = text.lower()
    for k in ("telegram_bot_token", "bot_token"):
        assert k not in low, f"forbidden key '{k}' appears in response"


def test_no_telegram_token_leak_anywhere(session):
    endpoints = [
        ("GET", "/api/system/status"),
        ("GET", "/api/settings"),
        ("GET", "/api/notifications/settings"),
        ("POST", "/api/notifications/telegram/test"),
    ]
    for method, path in endpoints:
        r = session.request(method, f"{BASE_URL}{path}",
                            json={} if method == "POST" else None, timeout=20)
        assert r.status_code in (200, 204), f"{path} => {r.status_code}"
        _no_token_leak(r.text)


# ---------- Regression: system status still correct ----------

def test_system_status_regression():
    r = requests.get(f"{BASE_URL}/api/system/status", timeout=15)
    assert r.status_code == 200
    d = r.json()
    # depending on shape, be permissive
    flat = str(d).lower()
    assert "not_configured" in flat or "kotak" in flat
    assert "mock" in flat or "demo" in flat
