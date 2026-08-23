"""
Iteration 55 retest — BUG 1b agenda READ-first prioriteit fix.

Fix: /app/backend/modules/chat/routes.py — READ-intent (si.detect_agenda_intent)
draait nu VOOR CREATE-intent (agenda_intent_service.detect_agenda_intent).
Nieuwe pattern 'uit de agenda halen/lezen/kijken' in _AGENDA_PATTERNS.

Regressie: CREATE-intent moet nog werken voor echte create-cases.
"""
import os
import re
import pytest
import requests
from pathlib import Path


def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if url:
        return url.rstrip("/")
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL"):
                return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


BASE_URL = _load_backend_url()
USER_ID = "user-001"

FAKE_TOOL_RX = re.compile(r"(\[agenda_[a-z]+)|(⚙️\s*agenda_)|(agenda_lezen\s*[→>])", re.IGNORECASE)


def _post(session_id: str, message: str) -> dict:
    r = requests.post(
        f"{BASE_URL}/api/chat/message",
        json={"user_id": USER_ID, "session_id": session_id, "message": message},
        timeout=90,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:300]}"
    return r.json()


def _no_fake_tool(msg: str):
    m = FAKE_TOOL_RX.search(msg or "")
    assert not m, f"Fake tool-syntax: {m.group(0)!r} in {msg!r}"


# ---- BUG 1b: READ-intent wint van CREATE ----
def test_bug_1b_afspraak_uit_agenda_halen_is_read():
    data = _post("retest-1b", "zou jij mijn afspraak van aanstaande dinsdag uit de agenda willen halen")
    rtype = data.get("type", "")
    msg = data.get("message", "") or ""
    print(f"[1b] type={rtype} msg={msg[:300]}")
    assert rtype == "agenda_overview", f"Verwacht agenda_overview, kreeg {rtype!r}. Msg: {msg[:200]}"
    _no_fake_tool(msg)
    # Verwacht echte agenda data — Tuin bij Roeline in user-001.json
    assert "roeline" in msg.lower() or "tuin" in msg.lower(), \
        f"Agenda-inhoud (Tuin bij Roeline) niet in bericht: {msg[:300]}"


# ---- BUG 1: dinsdag basiscase ----
def test_bug_1_dinsdag_agenda_overview():
    data = _post("retest-1", "wat staat er voor dinsdag")
    rtype = data.get("type", "")
    msg = data.get("message", "") or ""
    print(f"[1] type={rtype} msg={msg[:300]}")
    assert rtype == "agenda_overview", f"Verwacht agenda_overview, kreeg {rtype!r}"
    _no_fake_tool(msg)
    assert "roeline" in msg.lower() or "tuin" in msg.lower(), \
        f"Tuin bij Roeline niet in msg: {msg[:300]}"


# ---- BUG 1c: vrijdag ----
def test_bug_1c_vrijdag_agenda_response():
    data = _post("retest-1c", "wat staat er voor vrijdag")
    rtype = data.get("type", "")
    msg = data.get("message", "") or ""
    print(f"[1c] type={rtype} msg={msg[:300]}")
    assert rtype in ("agenda_overview", "capability_response"), f"Onverwacht type {rtype!r}"
    _no_fake_tool(msg)


# ---- Regressie: vandaag/morgen — minor type-label mag capability_response zijn ----
def test_regressie_vandaag_agenda_content():
    data = _post("retest-vandaag", "wat staat er vandaag")
    rtype = data.get("type", "")
    msg = data.get("message", "") or ""
    print(f"[vandaag] type={rtype} msg={msg[:300]}")
    assert rtype in ("agenda_overview", "capability_response"), f"Onverwacht type {rtype!r}"
    _no_fake_tool(msg)


def test_regressie_morgen_agenda_content():
    data = _post("retest-morgen", "wat staat er morgen")
    rtype = data.get("type", "")
    msg = data.get("message", "") or ""
    print(f"[morgen] type={rtype} msg={msg[:300]}")
    assert rtype in ("agenda_overview", "capability_response"), f"Onverwacht type {rtype!r}"
    _no_fake_tool(msg)


# ---- Regressie: CREATE-intent moet nog werken ----
def test_create_intent_tandarts_still_agenda_proposal():
    data = _post("retest-create", "ik heb morgen om 14:00 een afspraak met de tandarts")
    rtype = data.get("type", "")
    msg = data.get("message", "") or ""
    print(f"[create] type={rtype} msg={msg[:300]}")
    assert rtype == "agenda_proposal", \
        f"CREATE-intent gebroken: verwacht agenda_proposal, kreeg {rtype!r}. Msg: {msg[:200]}"
