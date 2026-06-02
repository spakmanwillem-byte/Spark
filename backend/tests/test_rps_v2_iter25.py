"""
v6_rps_002 — Spark Core 2.0 RPS V2 additions:
- Short chat triggers ('speel steen', etc.)
- Channel-aware opponent (spark vs bot)
- Random bot selection (5 bots)
- Easy bots (no learning) vs spark/bot-dood (learning first 10)
- Live KB image lookup for denkt_na card
- /api/help/for-viewer exposes RPS topic
- All 10 RPS KB cards tagged with 'sps'
"""
import json
import os
from pathlib import Path
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or (
    Path("/app/frontend/.env").read_text().split("REACT_APP_BACKEND_URL=")[1].splitlines()[0].strip()
)
API = f"{BASE_URL}/api"

KB_DIR = Path("/app/backend/data/knowledge/v2")

EASY_BOTS = {"bot-madelief", "bot-harry", "bot-smith", "bot-boekhouder"}
HARD_OPPS = {"spark", "bot-dood"}
ALL_BOTS = EASY_BOTS | {"bot-dood"}


# ---------- Chat triggers ----------
class TestChatTriggers:
    def test_short_trigger_speel_steen_spark(self):
        r = requests.post(f"{API}/chat/message",
                          json={"message": "speel steen", "user_id": "user-001", "channel": "spark"})
        assert r.status_code == 200
        d = r.json()
        assert d.get("action") == "open_game_rps", d
        assert d.get("rps_opponent") == "spark"
        assert "Steen" in (d.get("message") or "") or "Papier" in (d.get("message") or "")

    def test_full_trigger_speel_steen_papier_schaar_spark(self):
        r = requests.post(f"{API}/chat/message",
                          json={"message": "speel steen papier schaar", "user_id": "user-001", "channel": "spark"})
        assert r.status_code == 200
        d = r.json()
        assert d.get("action") == "open_game_rps"
        assert d.get("rps_opponent") == "spark"

    def test_short_trigger_speel_papier_spark(self):
        r = requests.post(f"{API}/chat/message",
                          json={"message": "speel papier", "user_id": "user-001", "channel": "spark"})
        assert r.status_code == 200
        assert r.json().get("action") == "open_game_rps"

    def test_community_channel_opponent_is_bot(self):
        r = requests.post(f"{API}/chat/message",
                          json={"message": "speel sps", "user_id": "user-001", "channel": "community"})
        assert r.status_code == 200
        d = r.json()
        assert d.get("action") == "open_game_rps"
        assert d.get("rps_opponent") == "bot"

    def test_spark_channel_opponent_is_spark(self):
        r = requests.post(f"{API}/chat/message",
                          json={"message": "spelletje sps", "user_id": "user-001", "channel": "spark"})
        assert r.status_code == 200
        assert r.json().get("rps_opponent") == "spark"


# ---------- Bot start (random pick) ----------
class TestBotStart:
    def test_start_bot_assigns_one_of_5_bots(self):
        seen = set()
        for i in range(12):
            r = requests.post(f"{API}/games/rps/start",
                              params={"user_id": f"TEST_iter25_rnd_{i}", "opponent": "bot"})
            assert r.status_code == 200
            opp = r.json()["session"]["opponent"]
            assert opp in ALL_BOTS, f"Unexpected opponent: {opp}"
            seen.add(opp)
        # Allow some randomness — at least 2 different bots in 12 tries
        assert len(seen) >= 2, f"Only saw bots: {seen}"

    def test_start_explicit_bot_madelief(self):
        r = requests.post(f"{API}/games/rps/start",
                          params={"user_id": "TEST_iter25_madelief", "opponent": "bot-madelief"})
        assert r.status_code == 200
        assert r.json()["session"]["opponent"] == "bot-madelief"


# ---------- Learning flag ----------
class TestLearningFlag:
    def test_easy_bot_never_learns(self):
        uid = "TEST_iter25_easy_learn"
        requests.post(f"{API}/games/rps/start",
                      params={"user_id": uid, "opponent": "bot-harry"})
        for _ in range(3):
            r = requests.post(f"{API}/games/rps/play",
                              json={"user_id": uid, "choice": "steen"})
            assert r.status_code == 200
            d = r.json()
            assert d["opponent"] == "bot-harry"
            assert d["spark_is_learning"] is False, "Easy bot should not be learning"

    def test_spark_is_learning_first_round(self):
        uid = "TEST_iter25_spark_learn"
        # Clear learning history by using a fresh user id
        # Make sure session opponent = spark
        requests.post(f"{API}/games/rps/start",
                      params={"user_id": uid, "opponent": "spark"})
        # Reset learning history if exists (history file is shared) — use fresh uid
        # First play should have history<10 => learning=True
        r = requests.post(f"{API}/games/rps/play",
                          json={"user_id": uid, "choice": "steen"})
        d = r.json()
        # If a previous test created history, this might be >=10. Use fresh uid above.
        assert d["opponent"] == "spark"
        # history_length is the cumulative after this play. If <=10 then was learning
        if d["history_length"] <= 10:
            assert d["spark_is_learning"] is True

    def test_bot_dood_learns_first_10(self):
        uid = "TEST_iter25_dood_learn"
        requests.post(f"{API}/games/rps/start",
                      params={"user_id": uid, "opponent": "bot-dood"})
        r = requests.post(f"{API}/games/rps/play",
                          json={"user_id": uid, "choice": "papier"})
        d = r.json()
        assert d["opponent"] == "bot-dood"
        if d["history_length"] <= 10:
            assert d["spark_is_learning"] is True


# ---------- Cards endpoint with live image lookup ----------
class TestCardsImages:
    def test_denkt_na_has_image(self):
        r = requests.get(f"{API}/games/rps/cards")
        assert r.status_code == 200
        cards = r.json().get("cards", {})
        assert "denkt_na" in cards
        img = cards["denkt_na"].get("image")
        assert img is not None and img != "", f"denkt_na image missing: {cards['denkt_na']}"
        assert "c6b518680717" in img, f"Expected file c6b518680717 in image url: {img}"

    def test_all_10_cards_have_images(self):
        r = requests.get(f"{API}/games/rps/cards")
        cards = r.json().get("cards", {})
        expected = {"steen", "papier", "schaar", "gewonnen", "verloren",
                    "denkt_na", "maak_een_keus", "score", "high_score", "stop"}
        assert set(cards.keys()) >= expected, f"Missing card keys: {expected - set(cards.keys())}"
        missing_img = [k for k in expected if not cards[k].get("image")]
        assert not missing_img, f"Cards missing images: {missing_img}"


# ---------- Help endpoint ----------
class TestHelpEndpoint:
    def test_help_for_viewer_user_001_has_rps_topic(self):
        r = requests.get(f"{API}/help/for-viewer", params={"user_id": "user-001"})
        assert r.status_code == 200
        d = r.json()
        topics = d.get("topics") or d.get("items") or []
        assert isinstance(topics, list) and len(topics) > 0
        rps_topic = next((t for t in topics if (t.get("id") or "").lower() == "rps"), None)
        assert rps_topic is not None, f"No RPS topic. Topic ids: {[t.get('id') for t in topics]}"
        label = (rps_topic.get("label") or rps_topic.get("title") or "")
        assert "Steen-Papier-Schaar" in label or "steen" in label.lower(), f"Bad label: {label}"


# ---------- KB tags ----------
class TestKBSpsTags:
    def test_10_sps_cards_exist(self):
        sps_cards = []
        for f in ("doen", "weten", "spreken", "voelen"):
            p = KB_DIR / f"knowledge_v2_{f}.json"
            if not p.exists():
                continue
            data = json.loads(p.read_text())
            items = data.get("items") or data.get("cards") or []
            if not items and isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        items = v
                        break
            for it in items:
                if "sps" in (it.get("tags") or []):
                    sps_cards.append({"id": it.get("id"), "file": f})
        assert len(sps_cards) == 10, f"Expected 10 sps-tagged cards, found {len(sps_cards)}: {sps_cards}"
