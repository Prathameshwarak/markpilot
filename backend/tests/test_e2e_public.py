"""End-to-end backend API tests against the public preview URL (Milestone 1)."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://marketpilot-equity.preview.emergentagent.com").rstrip("/")
DEMO_EMAIL = "demo@marketpilot.in"
DEMO_PASSWORD = "Demo1234!"


@pytest.fixture(scope="module")
def demo_session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD})
    assert r.status_code == 200, r.text
    token = s.cookies.get("access_token")
    if token:
        s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# ---------- Health / system ----------
def test_health():
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200 and r.json()["status"] == "healthy"


def test_system_status():
    body = requests.get(f"{BASE_URL}/api/system/status").json()
    assert body["broker"]["order_execution"] == "disabled"
    assert body["modules"]["fno"] == "coming_soon"
    assert body["modules"]["equity"] == "active"


# ---------- Auth ----------
def test_register_login_me_logout():
    s = requests.Session(); s.headers.update({"Content-Type": "application/json"})
    email = f"test_{uuid.uuid4().hex[:8]}@example.org"
    r = s.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": "Passw0rd!", "name": "Tester"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == email
    r_me = s.get(f"{BASE_URL}/api/auth/me")
    assert r_me.status_code == 200 and r_me.json()["email"] == email
    assert s.post(f"{BASE_URL}/api/auth/logout").status_code == 200
    assert s.get(f"{BASE_URL}/api/auth/me").status_code == 401


def test_login_demo(demo_session):
    r = demo_session.get(f"{BASE_URL}/api/auth/me")
    assert r.status_code == 200 and r.json()["email"] == DEMO_EMAIL


def test_login_wrong_password():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": DEMO_EMAIL, "password": "wrong-xxx"})
    assert r.status_code == 401


def test_protected_route_rejects_unauth():
    r = requests.get(f"{BASE_URL}/api/monitoring")
    assert r.status_code == 401


# ---------- Equities ----------
def test_equities_list():
    body = requests.get(f"{BASE_URL}/api/equities").json()
    assert body["count"] >= 10
    e = body["equities"][0]
    assert "symbol" in e and "scores" in e and "overall" in e["scores"]


def test_equity_detail_and_research():
    sym = requests.get(f"{BASE_URL}/api/equities").json()["equities"][0]["symbol"]
    d = requests.get(f"{BASE_URL}/api/equities/{sym}").json()
    assert d["symbol"] == sym
    body = requests.get(f"{BASE_URL}/api/equities/{sym}/research").json()
    opp = body["opportunity"]
    assert opp["max"] == 100 and 0 <= opp["total"] <= 100
    for k in ("technical", "fundamental", "sentiment", "sector", "risk_reward"):
        assert k in opp["breakdown"], f"missing {k}"
    # 35/25/15/10/15 caps
    caps = {b: opp["breakdown"][b]["max"] for b in opp["breakdown"]}
    assert caps == {"technical": 35, "fundamental": 25, "sentiment": 15, "sector": 10, "risk_reward": 15}


def test_market_overview():
    body = requests.get(f"{BASE_URL}/api/market/overview").json()
    assert "nifty" in body and "regime" in body
    assert "sector_performance" in body
    assert "top_gainers" in body and "top_losers" in body


# ---------- Trade ideas + monitoring ----------
def test_trade_ideas_public():
    body = requests.get(f"{BASE_URL}/api/trade-ideas").json()
    assert body["count"] > 0
    idea = body["ideas"][0]
    assert idea["id"].startswith("idea-")
    for k in ("entry", "stop_loss", "target1", "target2", "score", "risk_reward"):
        assert k in idea


def test_monitor_refresh_close_flow(demo_session):
    ideas = requests.get(f"{BASE_URL}/api/trade-ideas").json()["ideas"]
    idea_id = ideas[0]["id"]
    r = demo_session.post(f"{BASE_URL}/api/trade-ideas/{idea_id}/monitor")
    assert r.status_code == 200, r.text
    session_id = r.json()["id"]
    assert r.json()["status"] == "MONITORING"
    lst = demo_session.get(f"{BASE_URL}/api/monitoring")
    assert lst.status_code == 200 and lst.json()["count"] >= 1
    rr = demo_session.post(f"{BASE_URL}/api/monitoring/{session_id}/refresh")
    assert rr.status_code == 200, rr.text
    rc = demo_session.post(f"{BASE_URL}/api/monitoring/{session_id}/close")
    assert rc.status_code == 200, rc.text


# ---------- Alerts / journal ----------
def test_alerts_list(demo_session):
    r = demo_session.get(f"{BASE_URL}/api/alerts")
    assert r.status_code == 200 and "alerts" in r.json()


def test_journal_create_and_list(demo_session):
    payload = {
        "symbol": "TESTSYM", "setup": "Swing", "direction": "bullish",
        "entry_price": 100.0, "exit_price": 110.0, "quantity": 10,
        "outcome": "win", "notes": "TEST_entry",
    }
    r = demo_session.post(f"{BASE_URL}/api/journal", json=payload)
    assert r.status_code == 200, r.text
    r2 = demo_session.get(f"{BASE_URL}/api/journal")
    assert r2.status_code == 200
    data = r2.json()
    entries = data.get("entries", data if isinstance(data, list) else [])
    assert any(e.get("symbol") == "TESTSYM" for e in entries)


# ---------- Settings ----------
def test_settings_get_and_update(demo_session):
    assert demo_session.get(f"{BASE_URL}/api/settings").status_code == 200
    payload = {"max_risk_pct": 1.5, "stop_buffer_pct": 0.5, "max_open_positions": 5,
               "telegram_enabled": False, "in_app_notifications": True, "persona": "Swing Trader"}
    r = demo_session.put(f"{BASE_URL}/api/settings", json=payload)
    assert r.status_code == 200, r.text


# ---------- Forgot password: generic response ----------
def test_forgot_password_generic_response():
    r1 = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": DEMO_EMAIL})
    r2 = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={"email": f"not_{uuid.uuid4().hex[:6]}@nope.io"})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json() == r2.json()
