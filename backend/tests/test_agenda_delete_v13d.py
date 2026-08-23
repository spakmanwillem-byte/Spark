"""Regressie: Agenda DELETE hook via chat (v13d_agenda_delete_001, sessie 55).

Willem: "haal aanstaande dinsdag uit de agenda" → Spark moet direct de
delete-flow starten (matches tonen + bevestiging vragen), niet "gebruik de
agenda-tab" antwoorden.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import uuid

import pytest
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from server import app  # noqa

client = TestClient(app)

AGENDA_FP = Path(__file__).parent.parent / "data" / "agenda" / "user-001.json"


def _post_chat(text: str, session_id: str) -> dict:
    r = client.post("/api/chat/message", json={
        "message": text, "user_id": "user-001", "session_id": session_id,
    })
    return r.json()


def _seed(count: int, day_offset: int = 5, tag: str = "pytest-del") -> list[str]:
    """Voeg N test-events toe aan Willem's agenda; return de gemaakte IDs."""
    with open(AGENDA_FP) as f:
        data = json.load(f)
    target = datetime.now(timezone.utc) + timedelta(days=day_offset)
    ids = []
    for i in range(count):
        evid = f"{tag}-{uuid.uuid4().hex[:6]}"
        data["events"].append({
            "id": evid,
            "titel": f"{tag}-{i}",
            "date": target.replace(hour=9 + i, minute=0).isoformat(),
            "status": "upcoming",
            "source": "pytest",
        })
        ids.append(evid)
    with open(AGENDA_FP, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return ids


def _cleanup(ids: list[str]):
    with open(AGENDA_FP) as f:
        data = json.load(f)
    data["events"] = [e for e in data.get("events", []) if e.get("id") not in ids]
    with open(AGENDA_FP, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _clear_state():
    from modules.chat import session_state
    session_state.set_state("user-001", pending_agenda_delete=None)


class TestAgendaDeleteIntent:
    def test_detect_single_variants(self):
        from modules.chat import smart_intents_service as si
        cases = [
            "haal aanstaande dinsdag uit de agenda",
            "verwijder afspraak van morgen",
            "schrap Roeline uit de agenda",
            "annuleer afspraak",
            "wis afspraak van vrijdag",
        ]
        for t in cases:
            assert si.detect_agenda_delete_intent(t), f"missed: {t}"

    def test_read_not_confused_as_delete(self):
        from modules.chat import smart_intents_service as si
        # READ moet niet als DELETE geregistreerd worden
        assert not si.detect_agenda_delete_intent("wat staat er dinsdag")
        assert not si.detect_agenda_delete_intent("heb ik afspraken morgen")


class TestAgendaDeleteFlow:
    def test_single_match_confirms_and_deletes(self):
        _clear_state()
        ids = _seed(count=1, tag="pytest-single")
        sid = uuid.uuid4().hex
        # 1: start
        r1 = _post_chat("verwijder pytest-single uit de agenda", sid)
        assert r1.get("type") == "agenda_delete_confirm", f"got {r1}"
        assert "verwijderen" in (r1.get("message") or "").lower()
        # 2: bevestig
        r2 = _post_chat("ja", sid)
        assert r2.get("type") == "agenda_deleted"
        assert r2.get("removed_count") == 1
        # verify
        with open(AGENDA_FP) as f:
            data = json.load(f)
        remaining = {e.get("id") for e in data.get("events", [])}
        assert ids[0] not in remaining
        _cleanup(ids)

    def test_multi_match_pick_one(self):
        _clear_state()
        ids = _seed(count=3, tag="pytest-multi")
        sid = uuid.uuid4().hex
        r1 = _post_chat("verwijder pytest-multi uit de agenda", sid)
        assert r1.get("type") == "agenda_delete_choose"
        assert "3" in (r1.get("message") or "")
        r2 = _post_chat("1", sid)
        assert r2.get("type") == "agenda_delete_confirm"
        r3 = _post_chat("ja", sid)
        assert r3.get("type") == "agenda_deleted"
        assert r3.get("removed_count") == 1
        _cleanup(ids)

    def test_multi_match_alle(self):
        _clear_state()
        ids = _seed(count=2, tag="pytest-alle")
        sid = uuid.uuid4().hex
        r1 = _post_chat("verwijder pytest-alle uit de agenda", sid)
        assert r1.get("type") == "agenda_delete_choose"
        r2 = _post_chat("alle", sid)
        assert r2.get("type") == "agenda_delete_confirm"
        r3 = _post_chat("ja", sid)
        assert r3.get("type") == "agenda_deleted"
        assert r3.get("removed_count") == 2
        _cleanup(ids)

    def test_cancel_flow(self):
        _clear_state()
        ids = _seed(count=1, tag="pytest-cancel")
        sid = uuid.uuid4().hex
        r1 = _post_chat("verwijder pytest-cancel uit de agenda", sid)
        assert r1.get("type") == "agenda_delete_confirm"
        r2 = _post_chat("nee", sid)
        assert r2.get("type") == "agenda_delete_cancelled"
        # verify: event nog aanwezig
        with open(AGENDA_FP) as f:
            data = json.load(f)
        remaining = {e.get("id") for e in data.get("events", [])}
        assert ids[0] in remaining
        _cleanup(ids)


class TestIntentPatternStoreAPI:
    def test_list_endpoint(self):
        r = client.get("/api/triggers/intent-patterns")
        assert r.status_code == 200
        d = r.json()
        assert d["stats"]["total_intents"] >= 10
        assert "agenda_delete" in d["intent_groups"]

    def test_add_and_remove_pattern(self):
        payload = {"pattern": r"\bpytest_unique_marker_xyz\b"}
        r = client.post("/api/triggers/edit/intent/agenda_delete/add", json=payload)
        assert r.status_code == 200
        # Verify appeared in additions
        r2 = client.get("/api/triggers/intent-patterns")
        additions = r2.json()["intent_groups"]["agenda_delete"]["additions"]
        assert payload["pattern"] in additions
        # Verify matcher picks it up
        from modules.chat import intent_pattern_store as _s
        assert _s.match_any("agenda_delete", "trigger pytest_unique_marker_xyz here")
        # Delete
        r3 = client.delete(
            "/api/triggers/edit/intent/agenda_delete/pattern",
            params={"pattern": payload["pattern"]},
        )
        assert r3.status_code == 200

    def test_baseline_cannot_be_deleted(self):
        from modules.chat import intent_pattern_store as _s
        baseline_pat = _s.get_baseline("agenda_delete")[0]
        r = client.delete(
            "/api/triggers/edit/intent/agenda_delete/pattern",
            params={"pattern": baseline_pat},
        )
        assert r.status_code == 400
