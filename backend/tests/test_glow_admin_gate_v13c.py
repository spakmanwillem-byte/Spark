"""v13c_glow_admin_gate_001 — regressie voor admin-tab afscherming in glow-nav.

Bug: Spark stelde gewone users voor om naar admin-alleen routes (Kennisbank,
Roadmap, Users beheer) te navigeren. Fix: adminOnly-flag op registry-items
+ is_admin-parameter in navigate/registry/list endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from server import app  # /app/backend/server.py

client = TestClient(app)


def test_registry_non_admin_hides_admin_tabs():
    r = client.get("/api/tabs/registry?is_admin=false")
    assert r.status_code == 200
    tabs = r.json()["tabs"]
    ids = {t["id"] for t in tabs}
    # Admin tabs die verborgen moeten zijn
    assert "knowledge-v2" not in ids
    assert "roadmap" not in ids
    assert "spark-brain" not in ids
    assert "users" not in ids
    assert "settings" not in ids
    assert "analytics" not in ids
    # Deze wél zichtbaar
    assert "dashboard" in ids
    assert "archief" in ids


def test_registry_admin_shows_all():
    r = client.get("/api/tabs/registry?is_admin=true")
    assert r.status_code == 200
    tabs = r.json()["tabs"]
    ids = {t["id"] for t in tabs}
    assert "knowledge-v2" in ids
    assert "roadmap" in ids
    assert "settings" in ids


def test_navigate_non_admin_cannot_reach_admin_tab():
    r = client.post("/api/tabs/navigate", json={"q": "ga naar kennisbank", "is_admin": False})
    assert r.status_code == 200
    assert r.json()["success"] is False


def test_navigate_admin_reaches_admin_tab():
    r = client.post("/api/tabs/navigate", json={"q": "ga naar kennisbank", "is_admin": True})
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["match"]["id"] == "knowledge-v2"


def test_navigate_public_tab_werkt_voor_iedereen():
    for is_admin in (True, False):
        r = client.post("/api/tabs/navigate", json={"q": "open agenda", "is_admin": is_admin})
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert r.json()["match"]["id"] == "calendar"


def test_list_tabs_non_admin_filters():
    r = client.get("/api/tabs/tabs?is_admin=false")
    tabs = r.json()["tabs"]
    ids = {t["id"] for t in tabs}
    assert "knowledge-v2" not in ids
    assert "roadmap" not in ids


def test_default_no_is_admin_treats_as_non_admin():
    """Voorzichtigheids-fallback: zonder is_admin param = geen admin toegang."""
    r = client.get("/api/tabs/registry")
    tabs = r.json()["tabs"]
    ids = {t["id"] for t in tabs}
    assert "settings" not in ids
    assert "knowledge-v2" not in ids
