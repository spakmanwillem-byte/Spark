"""Tests voor KB v2 inbox dedupe-fix (v6_kbv2_dedupe_001).

Verifieert:
- GET /api/kb/v2/inbox response-shape (bevat `hidden_dupes_in_lade`)
- Geen kaart in inbox die ook gevuld in een lade zit
- POST /inbox/add met bestaand begrip in lade → existing=true, geen nieuwe kaart
- POST /inbox/add met nieuw uniek begrip → existing=false, +1 kaart
- POST /admin/dedupe-inbox?dry_run=true → removed=0
- Regressie: /stats, /classify
"""
import json
import os
import uuid
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback naar frontend/.env
    try:
        for line in Path("/app/frontend/.env").read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass

API = f"{BASE_URL}/api/kb/v2"

LADE_FILES = {
    "weten": "/app/backend/data/knowledge/v2/knowledge_v2_weten.json",
    "doen": "/app/backend/data/knowledge/v2/knowledge_v2_doen.json",
    "voelen": "/app/backend/data/knowledge/v2/knowledge_v2_voelen.json",
    "spreken": "/app/backend/data/knowledge/v2/knowledge_v2_spreken.json",
}


def _load_lade_begrippen_filled():
    """Return set of lowercase begrippen die in een lade staan met gevulde laag1."""
    filled = {}
    for lade, path in LADE_FILES.items():
        try:
            data = json.loads(Path(path).read_text())
        except Exception:
            continue
        kaarten = data.get("kaarten") or data.get("cards") or []
        if isinstance(data, list):
            kaarten = data
        for k in kaarten:
            begrip = (k.get("begrip") or "").strip().lower()
            lagen = k.get("lagen") or {}
            laag1 = lagen.get("laag1")
            if isinstance(laag1, dict):
                has_l1 = any(bool((v or "").strip()) for v in laag1.values() if isinstance(v, str))
            else:
                has_l1 = bool((laag1 or "").strip() if isinstance(laag1, str) else laag1)
            if begrip and has_l1:
                filled[begrip] = lade
    return filled


# ---------- Tests ----------

def test_inbox_shape_and_hidden_dupes_zero():
    r = requests.get(f"{API}/inbox", params={"limit": 500}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("success") is True
    assert "kaarten" in data
    assert "total" in data
    assert "hidden_dupes_in_lade" in data, f"missing hidden_dupes_in_lade: keys={list(data.keys())}"
    assert isinstance(data["hidden_dupes_in_lade"], int)
    assert data["hidden_dupes_in_lade"] >= 0
    # Na admin dedupe run:
    assert data["hidden_dupes_in_lade"] == 0, f"expected 0 after dedupe, got {data['hidden_dupes_in_lade']}"


def test_inbox_no_kaart_that_is_filled_in_lade():
    filled = _load_lade_begrippen_filled()
    r = requests.get(f"{API}/inbox", params={"limit": 500}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    offenders = []
    for k in data.get("kaarten", []):
        begrip = (k.get("begrip") or "").strip().lower()
        # inbox card zelf: check if laag1 empty
        lagen = k.get("lagen") or {}
        l1 = lagen.get("laag1")
        if isinstance(l1, dict):
            inbox_has_l1 = any(bool((v or "").strip()) for v in l1.values() if isinstance(v, str))
        else:
            inbox_has_l1 = bool(l1)
        if begrip in filled and not inbox_has_l1:
            offenders.append({"begrip": begrip, "lade": filled[begrip], "card_id": k.get("id") or k.get("card_id")})
    assert not offenders, f"Inbox bevat {len(offenders)} kaarten die al gevuld in lade staan: {offenders[:5]}"


def test_inbox_add_existing_in_lade_returns_existing_no_growth():
    # 'spinoza' zit in lade weten
    before = requests.get(f"{API}/inbox", params={"limit": 1}, timeout=30).json()
    total_before = before["total"]

    r = requests.post(f"{API}/inbox/add", json={"begrip": "spinoza", "user_id": "test-user"}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    # Must NOT create a new inbox card
    assert body.get("existing") is True, f"expected existing=true, got: {body}"
    assert body.get("lade") in ("weten", "doen", "voelen", "spreken"), f"expected lade, got: {body}"

    after = requests.get(f"{API}/inbox", params={"limit": 1}, timeout=30).json()
    total_after = after["total"]
    assert total_after == total_before, f"inbox groeide van {total_before} → {total_after}"


def test_inbox_add_new_unique_creates_card():
    unique = f"test-dupe-guard-{uuid.uuid4().hex[:8]}"
    before = requests.get(f"{API}/inbox", params={"limit": 1}, timeout=30).json()
    total_before = before["total"]

    r = requests.post(f"{API}/inbox/add", json={"begrip": unique, "user_id": "test-user"}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("existing") in (False, None), f"expected existing=false, got: {body}"
    assert body.get("success") is True or body.get("card_id") or body.get("id")

    after = requests.get(f"{API}/inbox", params={"limit": 1}, timeout=30).json()
    total_after = after["total"]
    assert total_after == total_before + 1, f"expected +1 (was {total_before}), got {total_after}"


def test_admin_dedupe_dry_run_zero():
    r = requests.post(f"{API}/admin/dedupe-inbox", params={"dry_run": "true"}, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    removed = body.get("removed", body.get("removed_count", body.get("count")))
    assert removed == 0, f"expected removed=0 na eerdere run, got: {body}"


def test_stats_regression():
    r = requests.get(f"{API}/stats", timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body.get("success") is True
    # per_lade of vergelijkbaar veld
    assert any(k in body for k in ("per_lade", "lades", "stats", "totals", "totalen", "inbox"))


def test_classify_regression():
    """Verplaats een inbox-kaart met _inbox_reason='missing_laag1' naar een lade."""
    r = requests.get(f"{API}/inbox", params={"limit": 200, "reason": "missing_laag1"}, timeout=30)
    if r.status_code != 200:
        pytest.skip("inbox list niet beschikbaar")
    kaarten = r.json().get("kaarten", [])
    # pak een verse test-dupe-guard kaart aan als beschikbaar, anders eerste met missing_laag1
    target = None
    for k in kaarten:
        if (k.get("begrip") or "").startswith("test-dupe-guard-"):
            target = k
            break
    if not target and kaarten:
        target = kaarten[0]
    if not target:
        pytest.skip("Geen inbox-kaart met missing_laag1 beschikbaar")

    card_id = target.get("id") or target.get("card_id")
    payload = {
        "card_id": card_id,
        "lade": "weten",
        "updates": {
            "lagen": {"laag1": "regressie-test-laag1-inhoud"}
        },
        "user_id": "test-user",
    }
    resp = requests.post(f"{API}/classify", json=payload, timeout=30)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("success") is True, f"classify faalde: {body}"
