"""v13d_notities_dagboek_terugblik_001 (sessie 56b) — Willem's hooks:
"hoeveel notities heb ik in augustus" / "wat is mijn laatste notitie" /
"wat schreef ik gisteren in mijn dagboek"."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, timezone
from modules.core.storage import save_json, load_json

TEST_USER = "user-terug-notes-test"
NOTES_FILE = Path("/app/backend/data/notes/notes.json")
DAGBOEK_FILE = Path("/app/backend/data/dagboek") / f"{TEST_USER}.json"


def setup_module(m):
    # Backup existing notes and append 4 test-notes for TEST_USER
    now = datetime.now(timezone.utc)
    gisteren = now - timedelta(days=1)
    twee_maanden_terug = now - timedelta(days=65)
    data = load_json(NOTES_FILE, default={"notes": []})
    data["notes"] = [n for n in data["notes"] if n.get("user_id") != TEST_USER]
    data["notes"].extend([
        {"id": "n1", "user_id": TEST_USER, "titel": "Idee voor tuin", "inhoud": "planten kopen",
         "categorie": "Observatie", "tags": [], "priority": "medium",
         "scope": "prive", "datum": now.isoformat()},
        {"id": "n2", "user_id": TEST_USER, "titel": "Factuur Jeroen", "inhoud": "5 uur werk",
         "categorie": "Werk", "tags": [], "priority": "high",
         "scope": "zakelijk", "datum": gisteren.isoformat()},
        {"id": "n3", "user_id": TEST_USER, "titel": "Oude aantekening", "inhoud": "iets van 2 maanden geleden",
         "categorie": "Observatie", "tags": [], "priority": "low",
         "scope": "prive", "datum": twee_maanden_terug.isoformat()},
        {"id": "n4", "user_id": TEST_USER, "titel": "Admin todo", "inhoud": "backup script maken",
         "categorie": "Admin", "tags": [], "priority": "medium",
         "scope": "admin", "datum": now.isoformat()},
    ])
    save_json(NOTES_FILE, data)
    # Dagboek
    save_json(DAGBOEK_FILE, {"entries": [
        {"id": "d1", "datum": gisteren.isoformat(), "mood": "blij", "content": "Was mooi zonnig weer"},
        {"id": "d2", "datum": now.isoformat(), "mood": "moe", "content": "Lange dag gewerkt"},
    ]})


def teardown_module(m):
    data = load_json(NOTES_FILE, default={"notes": []})
    data["notes"] = [n for n in data["notes"] if n.get("user_id") != TEST_USER]
    save_json(NOTES_FILE, data)
    if DAGBOEK_FILE.exists():
        DAGBOEK_FILE.unlink()


def test_notities_hoeveel_totaal():
    from modules.chat.capability_handler_service import _handle_notities_terugblik
    r = _handle_notities_terugblik(TEST_USER, "hoeveel notities heb ik")
    # 3 non-admin notes (n1, n2, n3); n4 (admin) uitgesloten
    assert r["count"] == 3
    assert "3" in r["message"]


def test_notities_laatste():
    from modules.chat.capability_handler_service import _handle_notities_terugblik
    r = _handle_notities_terugblik(TEST_USER, "wat is mijn laatste notitie")
    assert "Idee voor tuin" in r["message"] or "Factuur Jeroen" in r["message"]


def test_notities_scope_admin_uitgesloten():
    from modules.chat.capability_handler_service import _handle_notities_terugblik
    r = _handle_notities_terugblik(TEST_USER, "hoeveel notities")
    # n4 heeft scope admin en mag NIET meetellen
    assert "Admin todo" not in r["message"]


def test_notities_deze_maand():
    from modules.chat.capability_handler_service import _handle_notities_terugblik
    r = _handle_notities_terugblik(TEST_USER, "hoeveel notities heb ik deze maand")
    # n1 en n2 zitten in huidige maand (n3 = 2 maanden terug)
    assert r["count"] in (1, 2), f"got {r['count']}"


def test_dagboek_gisteren():
    from modules.chat.capability_handler_service import _handle_dagboek_terugblik
    r = _handle_dagboek_terugblik(TEST_USER, "wat schreef ik gisteren in mijn dagboek")
    assert "gisteren" in r["message"].lower()
    assert "Was mooi zonnig" in r["message"]


def test_dagboek_laatste():
    from modules.chat.capability_handler_service import _handle_dagboek_terugblik
    r = _handle_dagboek_terugblik(TEST_USER, "wat is mijn laatste dagboek")
    assert "moe" in r["message"].lower() or "Lange dag" in r["message"]


def test_router_notities():
    from modules.chat.capability_handler_service import route_capability
    r = route_capability("hoeveel notities heb ik", TEST_USER)
    assert r is not None
    assert r.get("capability_id") == "notities_terugblik"


def test_router_dagboek():
    from modules.chat.capability_handler_service import route_capability
    r = route_capability("wat schreef ik gisteren in mijn dagboek", TEST_USER)
    assert r is not None
    assert r.get("capability_id") == "dagboek_terugblik"


def test_notes_scope_default_prive():
    """Nieuwe note zonder scope → default 'prive'."""
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)
    res = client.post("/api/notes/create", json={
        "titel": "Test scope default", "inhoud": "x", "user_id": TEST_USER,
    })
    assert res.status_code == 200
    assert res.json()["note"]["scope"] == "prive"


def test_notes_scope_zakelijk_geaccepteerd():
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)
    res = client.post("/api/notes/create", json={
        "titel": "Zakelijk test", "inhoud": "x", "user_id": TEST_USER, "scope": "zakelijk",
    })
    assert res.status_code == 200
    assert res.json()["note"]["scope"] == "zakelijk"


def test_notes_scope_werk_wordt_prive():
    """Ongeldige scope-waarde (oude 'werk') → fallback naar 'prive'."""
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)
    res = client.post("/api/notes/create", json={
        "titel": "Ongeldig", "inhoud": "x", "user_id": TEST_USER, "scope": "werk",
    })
    assert res.status_code == 200
    assert res.json()["note"]["scope"] == "prive"
