"""
Tests for D&D World endpoints — NEW resources + steden drag features
(v6_dnd_resources_001 / v6_dnd_steden_drag_001)

Covers:
- GET  /api/dnd/world/resources                  (list + 8 types)
- POST /api/dnd/world/resources                  (admin → resource+game+kb cards)
- POST /api/dnd/world/resources (non-admin)      → 403
- PATCH /api/dnd/world/resources/{id}            (move on map)
- DELETE /api/dnd/world/resources/{id}           (cleanup)
- PATCH /api/dnd/world/steden/leeuwarden         (move Leeuwarden)
- PATCH /api/dnd/world/steden/leeuwarden (non-admin) → 403
- Image fetch via /api/system-archive/file/{id}
- Auto-created game-card in /api/dnd/spark-world/game-cards
- Auto-created KB v2 inbox card in inbox.json
- Regression: /fracties, /steden, /provincies still work
"""
import base64
import io
import json
import os
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback to read from frontend/.env
    env_file = Path("/app/frontend/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE_URL}/api"

ADMIN_USER = "user-001"
NON_ADMIN_USER = "user-574ac78e"
LEEUWARDEN_ID = "leeuwarden"
KB_INBOX_FILE = Path("/app/backend/data/knowledge/v2/inbox.json")

# 1x1 transparent PNG
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    yield s
    s.close()


@pytest.fixture(scope="module")
def created_resource_ids():
    """Collects resource ids created during the run for teardown."""
    ids = []
    yield ids
    # Teardown — best-effort delete
    for rid in ids:
        try:
            requests.delete(f"{API}/dnd/world/resources/{rid}", params={"user_id": ADMIN_USER}, timeout=10)
        except Exception:
            pass


@pytest.fixture(scope="module")
def original_leeuwarden(session):
    """Save current Leeuwarden coords + restore at teardown."""
    r = session.get(f"{API}/dnd/world/steden/{LEEUWARDEN_ID}", timeout=10)
    assert r.status_code == 200, f"Pre-read Leeuwarden failed: {r.status_code} {r.text}"
    stad = r.json().get("stad") or {}
    kaart = stad.get("kaart") or {}
    orig = {"x_pct": kaart.get("x_pct", 60.0), "y_pct": kaart.get("y_pct", 22.0)}
    yield orig
    # Restore
    try:
        session.patch(
            f"{API}/dnd/world/steden/{LEEUWARDEN_ID}",
            json={"user_id": ADMIN_USER, "x_pct": orig["x_pct"], "y_pct": orig["y_pct"]},
            timeout=10,
        )
    except Exception:
        pass


# --------------------------------------------------------------------------
# Regression: existing endpoints
# --------------------------------------------------------------------------
class TestRegressionExistingEndpoints:
    def test_get_fracties(self, session):
        r = session.get(f"{API}/dnd/world/fracties", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "fracties" in data
        assert isinstance(data["fracties"], list)
        assert len(data["fracties"]) >= 9  # baseline has 10 incl neutraal

    def test_get_provincies(self, session):
        r = session.get(f"{API}/dnd/world/provincies", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "provincies" in data and "fracties" in data
        assert len(data["provincies"]) == 12

    def test_get_steden(self, session):
        r = session.get(f"{API}/dnd/world/steden", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "steden" in data
        assert isinstance(data["steden"], list)


# --------------------------------------------------------------------------
# GET /resources — types must include all 8
# --------------------------------------------------------------------------
class TestResourcesList:
    EXPECTED_TYPE_IDS = {"vis", "bos", "akker", "mijn", "weide", "kruid", "steen", "anders"}

    def test_get_resources_returns_list_and_types(self, session):
        r = session.get(f"{API}/dnd/world/resources", timeout=10)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        data = r.json()
        assert "resources" in data
        assert isinstance(data["resources"], list)
        assert "types" in data
        type_ids = {t["id"] for t in data["types"]}
        assert type_ids == self.EXPECTED_TYPE_IDS, f"Mismatch types: {type_ids}"
        # Validate each type-entry has required fields
        for t in data["types"]:
            assert {"id", "naam", "kleur", "icon", "beschrijving"}.issubset(t.keys())


# --------------------------------------------------------------------------
# POST /resources — admin happy path + auto cards + image fetch
# --------------------------------------------------------------------------
class TestCreateResource:
    def test_create_resource_admin_success(self, session, created_resource_ids):
        files = {"image": ("TEST_resource.png", io.BytesIO(PNG_1X1), "image/png")}
        data = {
            "naam": "TEST_Visgrond_Noord",
            "type": "vis",
            "x_pct": "45.5",
            "y_pct": "30.0",
            "beschrijving": "Test vis area",
            "user_id": ADMIN_USER,
            "create_kb_card": "true",
        }
        r = session.post(f"{API}/dnd/world/resources", files=files, data=data, timeout=20)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        body = r.json()
        assert body.get("success") is True
        res = body.get("resource")
        assert res is not None
        assert res["id"].startswith("res-")
        assert res["naam"] == "TEST_Visgrond_Noord"
        assert res["type"] == "vis"
        assert res["kaart"]["x_pct"] == 45.5
        assert res["kaart"]["y_pct"] == 30.0
        assert res["image_url"], "image_url must be set"
        assert res["archive_id"], "archive_id must be set"
        assert res["linked_card_id"], "linked_card_id (game-xxx) must be set"
        assert res["linked_card_id"].startswith("game-")
        assert res["linked_kb_card_id"], "linked_kb_card_id (kb-xxx) must be set"
        assert res["linked_kb_card_id"].startswith("kb-")
        created_resource_ids.append(res["id"])
        # Store for downstream tests
        pytest.shared_resource = res

    def test_image_fetchable_via_system_archive(self, session):
        res = getattr(pytest, "shared_resource", None)
        assert res, "previous test must have created resource"
        url = f"{BASE_URL}{res['image_url']}"
        r = session.get(url, timeout=10)
        assert r.status_code == 200, f"Image fetch failed: {r.status_code}"
        assert len(r.content) > 0
        ctype = r.headers.get("content-type", "")
        assert "image" in ctype.lower() or "octet" in ctype.lower(), f"Unexpected content-type: {ctype}"

    def test_game_card_auto_created(self, session):
        res = getattr(pytest, "shared_resource", None)
        assert res, "previous test must have created resource"
        r = session.get(f"{API}/dnd/spark-world/game-cards", timeout=10)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        data = r.json()
        cards = data.get("cards") or data.get("game_cards") or []
        if isinstance(cards, dict):
            cards = list(cards.values())
        target = next((c for c in cards if c.get("id") == res["linked_card_id"]), None)
        assert target is not None, f"Auto-created game card {res['linked_card_id']} not found in {len(cards)} cards"
        assert target.get("class") == "game"
        gm = target.get("game_meta") or {}
        assert gm.get("kind") == "resource"
        assert gm.get("resource_type") == "vis"
        assert gm.get("resource_id") == res["id"]
        media = target.get("media") or {}
        image_urls = media.get("image_urls") or []
        assert len(image_urls) >= 1
        assert image_urls[0] == res["image_url"]

    def test_kb_inbox_card_auto_created(self):
        """Read inbox.json directly since KB API may not expose by id."""
        res = getattr(pytest, "shared_resource", None)
        assert res, "previous test must have created resource"
        assert KB_INBOX_FILE.exists(), f"{KB_INBOX_FILE} not found"
        data = json.loads(KB_INBOX_FILE.read_text())
        kaarten = data.get("kaarten") or []
        target = next((k for k in kaarten if k.get("id") == res["linked_kb_card_id"]), None)
        assert target is not None, f"KB inbox card {res['linked_kb_card_id']} missing"
        assert target.get("begrip") == res["naam"]
        tags = target.get("tags") or []
        assert "grondstof" in tags, f"'grondstof' tag missing in {tags}"
        assert "vis" in tags

    def test_create_resource_non_admin_forbidden(self, session):
        files = {"image": ("TEST_forbidden.png", io.BytesIO(PNG_1X1), "image/png")}
        data = {
            "naam": "TEST_Forbidden",
            "type": "bos",
            "x_pct": "10",
            "y_pct": "10",
            "user_id": NON_ADMIN_USER,
        }
        r = session.post(f"{API}/dnd/world/resources", files=files, data=data, timeout=15)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"


# --------------------------------------------------------------------------
# PATCH /resources/{id}
# --------------------------------------------------------------------------
class TestPatchResource:
    def test_patch_resource_coords(self, session):
        res = getattr(pytest, "shared_resource", None)
        assert res, "shared resource needed"
        rid = res["id"]
        r = session.patch(
            f"{API}/dnd/world/resources/{rid}",
            json={"user_id": ADMIN_USER, "x_pct": 33.0, "y_pct": 42.0},
            timeout=10,
        )
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        body = r.json()
        assert body["success"] is True
        assert body["resource"]["kaart"]["x_pct"] == 33.0
        assert body["resource"]["kaart"]["y_pct"] == 42.0

        # GET verifies persistence
        r2 = session.get(f"{API}/dnd/world/resources", timeout=10)
        rs = r2.json()["resources"]
        target = next((x for x in rs if x["id"] == rid), None)
        assert target is not None
        assert target["kaart"]["x_pct"] == 33.0
        assert target["kaart"]["y_pct"] == 42.0

    def test_patch_resource_non_admin_forbidden(self, session):
        res = getattr(pytest, "shared_resource", None)
        assert res
        r = session.patch(
            f"{API}/dnd/world/resources/{res['id']}",
            json={"user_id": NON_ADMIN_USER, "x_pct": 5, "y_pct": 5},
            timeout=10,
        )
        assert r.status_code == 403

    def test_patch_resource_not_found(self, session):
        r = session.patch(
            f"{API}/dnd/world/resources/res-nonexistent-zzz",
            json={"user_id": ADMIN_USER, "x_pct": 1, "y_pct": 1},
            timeout=10,
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------
# PATCH /steden/{id} — Leeuwarden drag
# --------------------------------------------------------------------------
class TestPatchSteden:
    def test_patch_leeuwarden_admin(self, session, original_leeuwarden):
        new_x, new_y = 61.5, 23.7
        r = session.patch(
            f"{API}/dnd/world/steden/{LEEUWARDEN_ID}",
            json={"user_id": ADMIN_USER, "x_pct": new_x, "y_pct": new_y},
            timeout=10,
        )
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        body = r.json()
        assert body["success"] is True
        stad = body["stad"]
        assert stad["kaart"]["x_pct"] == new_x
        assert stad["kaart"]["y_pct"] == new_y

        # GET verifies persistence
        r2 = session.get(f"{API}/dnd/world/steden/{LEEUWARDEN_ID}", timeout=10)
        assert r2.status_code == 200
        kaart = r2.json()["stad"]["kaart"]
        assert kaart["x_pct"] == new_x
        assert kaart["y_pct"] == new_y

    def test_patch_leeuwarden_non_admin_forbidden(self, session):
        r = session.patch(
            f"{API}/dnd/world/steden/{LEEUWARDEN_ID}",
            json={"user_id": NON_ADMIN_USER, "x_pct": 99, "y_pct": 99},
            timeout=10,
        )
        assert r.status_code == 403

    def test_patch_steden_not_found(self, session):
        r = session.patch(
            f"{API}/dnd/world/steden/non-existent-city-zzz",
            json={"user_id": ADMIN_USER, "x_pct": 1, "y_pct": 1},
            timeout=10,
        )
        assert r.status_code == 404


# --------------------------------------------------------------------------
# DELETE /resources/{id}
# --------------------------------------------------------------------------
class TestDeleteResource:
    def test_delete_resource_admin(self, session, created_resource_ids):
        res = getattr(pytest, "shared_resource", None)
        assert res
        rid = res["id"]
        r = session.delete(f"{API}/dnd/world/resources/{rid}", params={"user_id": ADMIN_USER}, timeout=10)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        body = r.json()
        assert body["success"] is True
        assert body["deleted"] == rid

        # Verify removed
        r2 = session.get(f"{API}/dnd/world/resources", timeout=10)
        ids = [x["id"] for x in r2.json()["resources"]]
        assert rid not in ids
        if rid in created_resource_ids:
            created_resource_ids.remove(rid)

    def test_delete_resource_non_admin_forbidden(self, session, created_resource_ids):
        # Create a fresh resource as admin first for this test
        files = {"image": ("TEST_del.png", io.BytesIO(PNG_1X1), "image/png")}
        data = {
            "naam": "TEST_DeleteForbidden",
            "type": "steen",
            "x_pct": "20",
            "y_pct": "20",
            "user_id": ADMIN_USER,
            "create_kb_card": "false",
        }
        r = session.post(f"{API}/dnd/world/resources", files=files, data=data, timeout=15)
        assert r.status_code == 200
        rid = r.json()["resource"]["id"]
        created_resource_ids.append(rid)

        r2 = session.delete(f"{API}/dnd/world/resources/{rid}", params={"user_id": NON_ADMIN_USER}, timeout=10)
        assert r2.status_code == 403

    def test_delete_resource_not_found(self, session):
        r = session.delete(
            f"{API}/dnd/world/resources/res-nonexistent-zzz",
            params={"user_id": ADMIN_USER},
            timeout=10,
        )
        assert r.status_code == 404
