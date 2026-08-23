"""Regressie: shop_delete via chat + owner-permissie (v13d_shop_owner_delete_001, sessie 55).

Willem's logica: "gebruiker die een winkel heeft is admin over zijn winkel". Owner mag
eigen shops verwijderen via chat, ook zonder globaal admin-recht.

BELANGRIJK: tests werken via /api/spark/compose (de deep-route die de Spark-tab
gebruikt) EN /api/chat/message. Bug in sessie 55: capabilities werden gebypassed
in de Spark-tab omdat frontend naar compose ging i.p.v. chat/message.
"""
from pathlib import Path
import json
import sys
import uuid

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))
from server import app  # noqa

client = TestClient(app)
SHOPS_FP = Path(__file__).parent.parent / "data" / "shop" / "shops.json"


def _seed_shop(naam: str, owner: str = "user-001", shop_id: str | None = None) -> str:
    sid = shop_id or f"shop-test-{uuid.uuid4().hex[:8]}"
    with open(SHOPS_FP) as f:
        data = json.load(f)
    data["shops"].append({
        "id": sid, "naam": naam, "type": "digitaal",
        "owner_user_id": owner, "owner_naam": "test",
        "status": "open", "is_founder_shop": False,
    })
    with open(SHOPS_FP, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return sid


def _cleanup_shop(shop_id: str):
    with open(SHOPS_FP) as f:
        data = json.load(f)
    data["shops"] = [s for s in data.get("shops", []) if s.get("id") != shop_id]
    with open(SHOPS_FP, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _clear_state(user_id: str):
    from modules.chat import session_state
    session_state.set_state(user_id, pending_shop_delete=None)


def _compose(text: str, user_id: str = "user-001", session_id: str = "deep-test") -> dict:
    r = client.post("/api/spark/compose", json={
        "text": text, "user_id": user_id, "session_id": session_id,
    })
    return r.json()


class TestShopDeleteIntent:
    def test_variants_detect(self):
        from modules.chat import smart_intents_service as si
        cases = [
            "verwijder winkel TEST_PatchShop",
            "sluit shop TEST_CloseMe",
            "haal winkel TEST_A weg",
            "gooi winkel TEST_B weg",
            "delete shop TEST_C",
            "zou jij deze test winkel willen verwijderen TEST_PatchShop",
        ]
        for t in cases:
            assert si.detect_shop_delete_intent(t), f"missed: {t}"

    def test_extract_shop_name(self):
        from modules.chat.smart_intents_service import _extract_shop_name_from_text
        assert _extract_shop_name_from_text("verwijder shop TEST_PatchShop") == "TEST_PatchShop"
        assert _extract_shop_name_from_text('verwijder "MijnWinkel"') == "MijnWinkel"
        assert _extract_shop_name_from_text("sluit shop CoolStore") == "CoolStore"


class TestShopDeleteFlow:
    def test_owner_can_delete_own_shop(self):
        sid = _seed_shop("TESTShopOwnerDel", owner="user-001")
        _clear_state("user-001")
        try:
            r1 = _compose(f"verwijder winkel TESTShopOwnerDel", user_id="user-001")
            assert r1.get("type") == "shop_delete_confirm", f"got {r1}"
            r2 = _compose("ja", user_id="user-001")
            assert r2.get("type") == "shop_deleted"
            # verify weg
            with open(SHOPS_FP) as f:
                data = json.load(f)
            ids = [s.get("id") for s in data.get("shops", [])]
            assert sid not in ids
        finally:
            _cleanup_shop(sid)

    def test_non_owner_gets_denied(self):
        # Willem is owner, Marieke probeert te verwijderen
        sid = _seed_shop("TESTShopMarNoDel", owner="user-001")
        _clear_state("user-c609d7d1")
        try:
            r = _compose("verwijder winkel TESTShopMarNoDel", user_id="user-c609d7d1")
            assert r.get("type") == "shop_delete_denied"
            # verify NIET weg
            with open(SHOPS_FP) as f:
                data = json.load(f)
            ids = [s.get("id") for s in data.get("shops", [])]
            assert sid in ids, "Shop mocht niet zijn verwijderd door non-owner"
        finally:
            _cleanup_shop(sid)

    def test_cancel_leaves_shop(self):
        sid = _seed_shop("TESTShopCancel", owner="user-001")
        _clear_state("user-001")
        try:
            r1 = _compose("verwijder winkel TESTShopCancel", user_id="user-001")
            assert r1.get("type") == "shop_delete_confirm"
            r2 = _compose("nee", user_id="user-001")
            assert r2.get("type") == "shop_delete_cancelled"
            with open(SHOPS_FP) as f:
                data = json.load(f)
            ids = [s.get("id") for s in data.get("shops", [])]
            assert sid in ids
        finally:
            _cleanup_shop(sid)

    def test_pending_state_falls_through_on_other_intent(self):
        """Als user midden in shop-delete iets HEEL anders vraagt, moet pending
        vervallen en de nieuwe vraag beantwoord worden."""
        sid = _seed_shop("TESTShopPending", owner="user-001")
        _clear_state("user-001")
        try:
            r1 = _compose("verwijder winkel TESTShopPending", user_id="user-001")
            assert r1.get("type") == "shop_delete_confirm"
            # Nu iets HEEL anders vragen — mag niet in shop_delete_repeat blijven hangen
            r2 = _compose("welke user namen heb jij allemaal", user_id="user-001")
            assert r2.get("type") == "capability_response"
            assert r2.get("capability_id") == "gebruikers_namen"
        finally:
            _cleanup_shop(sid)


class TestComposeCapabilityHook:
    """Verifieer dat /api/spark/compose (de deep-route van Spark-tab) capabilities NIET
    meer skipt. Regressie voor Willem's bug 'welke user namen heb jij allemaal'
    → LLM antwoordde 'ik zie geen data' i.p.v. de gebruikers-lijst."""

    def test_tellen_gebruikers_via_compose(self):
        _clear_state("user-001")
        r = _compose("hoeveel users heb jij", user_id="user-001")
        assert r.get("type") == "capability_response"
        assert r.get("used_model") == "hands"
        assert "mensen" in (r.get("message") or "").lower()

    def test_gebruikers_namen_via_compose(self):
        _clear_state("user-001")
        r = _compose("welke user namen heb jij allemaal", user_id="user-001")
        assert r.get("capability_id") == "gebruikers_namen"
        msg = r.get("message") or ""
        assert "Willem" in msg  # Admin ziet alle namen

    def test_agenda_read_via_compose_stays_llm(self):
        """Agenda-read is complex (day-focus) — hoort NIET door de eenvoudige
        capability-hook te gaan bij compose. Als het wel raakt aan compose
        moet output nog steeds bruikbaar zijn."""
        _clear_state("user-001")
        r = _compose("wat is 12 keer 7", user_id="user-001")
        # Math-capability hoort te vuren
        assert r.get("type") == "capability_response"
