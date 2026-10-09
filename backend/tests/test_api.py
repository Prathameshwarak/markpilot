import uuid
import pytest
from fastapi.testclient import TestClient
from server import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_system_status(client):
    r = client.get("/api/system/status")
    assert r.status_code == 200
    body = r.json()
    assert body["modules"]["fno"] == "coming_soon"
    assert body["broker"]["order_execution"] == "disabled"


def test_equities_and_ideas_public(client):
    r = client.get("/api/equities")
    assert r.status_code == 200
    assert r.json()["count"] > 0
    r2 = client.get("/api/trade-ideas")
    assert r2.status_code == 200
    assert r2.json()["count"] > 0


def test_register_login_me_flow(client):
    email = f"test_{uuid.uuid4().hex[:8]}@example.org"
    r = client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!", "name": "Tester"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == email
    # Secure cookies are not resent over http by TestClient; use the token as a Bearer header.
    token = client.cookies.get("access_token")
    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["email"] == email


def test_register_validation_short_password(client):
    r = client.post("/api/auth/register", json={"email": "x@example.org", "password": "123", "name": "X"})
    assert r.status_code == 422


def test_protected_route_requires_auth(client):
    fresh = TestClient(app)
    r = fresh.get("/api/monitoring")
    assert r.status_code == 401


def test_login_wrong_password(client):
    email = f"test_{uuid.uuid4().hex[:8]}@example.org"
    client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!", "name": "Tester"})
    r = client.post("/api/auth/login", json={"email": email, "password": "wrongpass"})
    assert r.status_code == 401


def test_monitor_idea_and_list(client):
    email = f"test_{uuid.uuid4().hex[:8]}@example.org"
    client.post("/api/auth/register", json={"email": email, "password": "Passw0rd!", "name": "Tester"})
    token = client.cookies.get("access_token")
    hdr = {"Authorization": f"Bearer {token}"}
    ideas = client.get("/api/trade-ideas").json()["ideas"]
    idea_id = ideas[0]["id"]
    r = client.post(f"/api/trade-ideas/{idea_id}/monitor", headers=hdr)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "MONITORING"
    r2 = client.get("/api/monitoring", headers=hdr)
    assert r2.status_code == 200
    assert r2.json()["count"] >= 1
