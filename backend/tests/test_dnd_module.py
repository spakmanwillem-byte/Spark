"""
D&D Module (v4_dnd_001) Backend Tests — iteration 20
Tests lore index, behavior tracking, aura computation, world-state, observations & spark greeting.
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
USER = "user-001"
EMPTY_USER = "user-empty-test"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ====== 1. Lore index ======
def test_lore_returns_avatars_and_behavior(client):
    r = client.get(f"{BASE_URL}/api/dnd/lore")
    assert r.status_code == 200
    data = r.json()
    avatars = data.get("avatars_as_functions", [])
    behavior = data.get("behavior_to_unlock", {})
    assert len(avatars) == 7
    names = {a["name"] for a in avatars}
    assert {"Het Eerste Licht", "De Reaper", "De Boekhouder"}.issubset(names)
    assert len(behavior) == 6
    assert "veel_helpen" in behavior


# ====== 2. POST /track ======
def test_track_increments_counter(client):
    # Track help_msg+1 and ensure persisted (does not reset existing — additive)
    r = client.post(f"{BASE_URL}/api/dnd/track", json={"user_id": USER, "counter_key": "help_msg", "delta": 1})
    assert r.status_code == 200
    j = r.json()
    assert j["success"] is True
    counters = j["counters"]
    assert counters.get("help_msg", 0) >= 1
    # Track again to ensure additive
    r2 = client.post(f"{BASE_URL}/api/dnd/track", json={"user_id": USER, "counter_key": "help_msg", "delta": 1})
    assert r2.json()["counters"]["help_msg"] >= counters["help_msg"] + 1


# ====== 3. GET aura user-001 ======
def test_aura_for_user_001(client):
    # Ensure help_msg>=3
    client.post(f"{BASE_URL}/api/dnd/track", json={"user_id": USER, "counter_key": "help_msg", "delta": 3})
    r = client.get(f"{BASE_URL}/api/dnd/aura/{USER}")
    assert r.status_code == 200
    data = r.json()
    assert "layers" in data
    layers = data["layers"]
    assert 1 <= len(layers) <= 3
    cats = {l["category"] for l in layers}
    # veel_helpen should be tracked
    assert "veel_helpen" in cats
    helpen = next(l for l in layers if l["category"] == "veel_helpen")
    assert helpen["label"] == "Veel helpen"
    assert helpen["color"] == "#22c55e"
    assert "primary_color" in data
    assert isinstance(data.get("unlocks"), list)


# ====== 4. GET aura empty user ======
def test_aura_empty_user(client):
    # use a clean empty user id
    eu = f"empty-{int(time.time())}"
    r = client.get(f"{BASE_URL}/api/dnd/aura/{eu}")
    assert r.status_code == 200
    data = r.json()
    assert data["layers"][0]["category"] == "leeg"


# ====== 5. world-state ======
def test_world_state(client):
    r = client.get(f"{BASE_URL}/api/dnd/world-state")
    assert r.status_code == 200
    data = r.json()
    entities = data.get("entities", [])
    assert len(entities) >= 7
    assert data.get("grand_total", 0) >= 1
    for e in entities:
        assert "score" in e and "ratio" in e and "name" in e


# ====== 6. POST observe ======
def test_observe_logs_event(client):
    r = client.post(f"{BASE_URL}/api/dnd/observe", json={
        "user_id": USER,
        "kind": "avatar_changed",
        "detail": {"title": "TestAvatarX"}
    })
    assert r.status_code == 200
    j = r.json()
    assert j["success"] is True
    assert j["event"]["kind"] == "avatar_changed"
    assert j["event"]["spoken"] is False


# ====== 7. GET observations ======
def test_list_observations(client):
    # Add a fresh observation first
    client.post(f"{BASE_URL}/api/dnd/observe", json={
        "user_id": USER, "kind": "avatar_changed", "detail": {"title": "FreshTitle"}
    })
    r = client.get(f"{BASE_URL}/api/dnd/observations/{USER}?only_unspoken=true&limit=5")
    assert r.status_code == 200
    data = r.json()
    obs = data["observations"]
    assert len(obs) >= 1
    assert all(o["user_id"] == USER for o in obs)
    assert all(o.get("spoken") is False for o in obs)


# ====== 8. spark-greeting marks as spoken / no repeat ======
def test_spark_greeting_then_no_repeat(client):
    # Clear all existing unspoken events to test no-repeat cleanly
    client.post(f"{BASE_URL}/api/dnd/observations/mark-spoken", json={"user_id": USER})
    # Seed exactly one fresh observation
    client.post(f"{BASE_URL}/api/dnd/observe", json={
        "user_id": USER, "kind": "avatar_changed", "detail": {"title": "GreetingTest"}
    })
    r1 = client.get(f"{BASE_URL}/api/dnd/spark-greeting/{USER}")
    assert r1.status_code == 200
    g1 = r1.json()
    assert g1["has_greeting"] is True
    assert "Ik merkte iets op" in g1["message"]
    # Mention should reference avatar change phrase
    assert "avatar" in g1["message"].lower() or "vibe" in g1["message"].lower()
    # Second call should not repeat (no fresh unspoken event)
    r2 = client.get(f"{BASE_URL}/api/dnd/spark-greeting/{USER}")
    g2 = r2.json()
    assert g2["has_greeting"] is False


# ====== 9. avatar/select triggers observation ======
def test_avatar_select_creates_observation(client):
    # First fetch a valid gallery avatar id
    r = client.get(f"{BASE_URL}/api/avatar/gallery")
    assert r.status_code == 200
    avatars = r.json().get("avatars", [])
    # pick a non-locked avatar
    pick = next((a for a in avatars if not a.get("locked")), None)
    assert pick is not None, "No unlocked gallery avatar available"
    aref = f"gallery:{pick['id']}"

    # Select the avatar
    sel = client.put(f"{BASE_URL}/api/avatar/select/{USER}", json={"avatar_ref": aref})
    assert sel.status_code == 200
    assert sel.json()["success"] is True

    # Now verify observation was created
    obs = client.get(f"{BASE_URL}/api/dnd/observations/{USER}?only_unspoken=true&limit=5").json()
    kinds = [o["kind"] for o in obs["observations"]]
    assert "avatar_changed" in kinds
    # Find that specific observation with title equal to pick['title']
    titles = [o["detail"].get("title") for o in obs["observations"] if o["kind"] == "avatar_changed"]
    assert pick.get("title") in titles
