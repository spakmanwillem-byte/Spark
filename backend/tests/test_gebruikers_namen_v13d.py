"""Regressie: gebruikers_namen capability (v13d_gebruikers_namen_001, sessie 55).

Willem's productie-log: "ik wil alle usernamen opgenoemd hebben" → Spark zei
"ga naar Admin-tab". Niet acceptabel. Deze test blokkeert die regressie.
"""
from pathlib import Path
import sys
import uuid

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from server import app  # noqa

client = TestClient(app)


class TestGebruikersNamenAdmin:
    def _post(self, text: str, user_id: str = "user-001") -> dict:
        r = client.post("/api/chat/message", json={
            "message": text, "user_id": user_id, "session_id": uuid.uuid4().hex,
        })
        return r.json()

    def test_variants_all_match_capability(self):
        variants = [
            "ik wil alle usernamen opgenoemd hebben",
            "noem alle gebruikers",
            "geef me alle namen",
            "wie zit er op spark",
            "gebruikerslijst",
            "alle gebruikers noemen",
            "toon alle usernames",
        ]
        for q in variants:
            d = self._post(q, user_id="user-001")
            assert d.get("capability_id") == "gebruikers_namen", (
                f"expected gebruikers_namen, got {d.get('capability_id')} for: {q}"
            )

    def test_admin_sees_all_names_grouped_by_gradatie(self):
        d = self._post("noem alle gebruikers", user_id="user-001")
        msg = d.get("message", "")
        # Admin ziet gradatie-buckets én de familie-namen (Lotus, Heidi)
        assert "G1" in msg
        assert "Willem" in msg
        # Lotus is G2 → moet zichtbaar zijn voor Willem (admin G1)
        assert "Lotus" in msg or "Heidi" in msg

    def test_non_admin_gets_filtered_list(self):
        # Marieke = G3, niet-admin. Mag alleen G3+ zien.
        d = self._post("noem alle usernamen", user_id="user-c609d7d1")
        msg = d.get("message", "")
        # Marieke mag Willem (G1) niet zien (te laag) en Lotus (G2) ook niet
        assert d.get("capability_id") == "gebruikers_namen"
        assert "admin-toegang" in msg
        # G3+ users wel zichtbaar
        assert "Marieke" in msg

    def test_no_leak_of_family_names_to_high_gradatie(self):
        # Emmy = G7, moet Willem's familie (Lotus, Heidi) NIET zien.
        # Zoek Emmy's user_id dynamisch:
        import json
        users_fp = Path(__file__).parent.parent / "data" / "system" / "users.json"
        users = json.loads(users_fp.read_text())["users"]
        emmy = next((u for u in users if "emmy" in (u.get("naam") or "").lower()), None)
        assert emmy, "Emmy user niet gevonden — testdata inconsistent"
        d = self._post("gebruikerslijst", user_id=emmy["id"])
        msg = d.get("message", "")
        assert "Lotus" not in msg
        assert "Heidi" not in msg
        assert "Willem" not in msg
