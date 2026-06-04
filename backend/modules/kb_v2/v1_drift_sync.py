"""
v6_kbv2_v1_drift_sync_001 — Sync drift tussen v1 (chat-detected drafts) en v2 (UI).

Probleem: wanneer Spark via chat een nieuw begrip detecteert ("januari"),
landt het in KB v1 met status=draft, lege lagen, maar NOOIT in KB v2.
Dus de user ziet het niet in de UI om in te vullen.

Oplossing: scan v1 voor drafts met lege laag1, en maak/synchroniseer een
INBOX-kaart in v2. Idempotent (skipt als begrip al ergens in v2 staat).

Filters:
- Skip zinnen (is_sentence flag, of begrip > 30 chars met spatie)
- Skip al-bestaande v2-kaarten (lade of inbox)
- Skip emojis-only
"""
import re
import uuid
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timezone

from modules.core.storage import load_json, save_json

DATA = Path(__file__).parent.parent.parent / "data"
KB_V1 = DATA / "knowledge" / "learned_knowledge" / "knowledge_base.json"
KB_V2 = DATA / "knowledge" / "v2"


def _is_sentence(begrip: str, entry: Dict) -> bool:
    """Filter out 'context-zin' entries die niet echt 1 begrip zijn."""
    if not begrip:
        return True
    md = entry.get("metadata") or {}
    if md.get("is_sentence"):
        return True
    tags = entry.get("tags") or []
    if "context-zin" in tags or "auto-generated" in tags and "knowledge-snap" in tags:
        # alleen als ook lang
        if len(begrip) > 25 or begrip.count(" ") >= 3:
            return True
    # Heuristic: te lang, of 4+ woorden → waarschijnlijk een zin
    if len(begrip) > 30:
        return True
    if begrip.count(" ") >= 3:
        return True
    return False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sync_v1_drafts_to_v2_inbox(dry_run: bool = False) -> Dict:
    """Hoofdfunctie. Returns summary dict."""
    kb1 = load_json(KB_V1, default={"knowledge_entries": []})
    v1_entries = kb1.get("knowledge_entries", [])

    inbox_f = KB_V2 / "knowledge_inbox.json"
    inbox = load_json(inbox_f, default={"kaarten": []})
    inbox_begrip = {(c.get("begrip") or "").lower().strip() for c in inbox.get("kaarten", [])}

    # Build v2 lade-presence map (begrip lowercase → True als met laag1)
    v2_in_lade = set()
    for lade in ("doen", "weten", "spreken", "voelen"):
        d = load_json(KB_V2 / f"knowledge_v2_{lade}.json", default={"kaarten": []})
        for c in d.get("kaarten", []):
            v2_in_lade.add((c.get("begrip") or "").lower().strip())

    candidates = []
    skipped_sentence = 0
    skipped_already_v2 = 0
    skipped_no_begrip = 0

    for e in v1_entries:
        b = (e.get("begrip") or "").strip()
        if not b:
            skipped_no_begrip += 1
            continue
        b_lc = b.lower().strip()
        # Skip sentences
        if _is_sentence(b, e):
            skipped_sentence += 1
            continue
        # Skip al in lade
        if b_lc in v2_in_lade:
            skipped_already_v2 += 1
            continue
        # Skip al in inbox
        if b_lc in inbox_begrip:
            skipped_already_v2 += 1
            continue
        # Skip emojis-only / hele korte tekens
        if not re.search(r"[a-zà-ÿ]", b.lower()):
            skipped_no_begrip += 1
            continue
        if len(b) < 2:
            skipped_no_begrip += 1
            continue
        # Skip drafts met lege laag1 als status=actief ↔ ja, we willen juist deze
        candidates.append({
            "begrip": b,
            "v1_id": e.get("id"),
            "v1_status": e.get("status"),
            "tags": e.get("tags") or [],
            "detected_by": e.get("detected_by"),
            "detected_at": e.get("detected_at") or e.get("created_at"),
        })

    if dry_run:
        return {
            "success": True, "dry_run": True,
            "would_add": len(candidates),
            "skipped_sentence": skipped_sentence,
            "skipped_already_v2": skipped_already_v2,
            "skipped_no_begrip": skipped_no_begrip,
            "preview": [c["begrip"] for c in candidates[:30]],
        }

    # Add to v2 inbox
    added = 0
    for c in candidates:
        new_card = {
            "id": f"kbv2-{uuid.uuid4().hex[:8]}",
            "begrip": c["begrip"],
            "lade": None,
            "status": "draft",
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
            "tags": c["tags"],
            "verbanden": [],
            "footnote": {
                "bron": "v1_drift_sync",
                "ingedeeld_door": None,
                "ingedeeld_op": None,
                "vorige_versie_v1": c["v1_id"],
                "vertrouwen": 0.3,
                "aangemaakt_door": c.get("detected_by"),
                "aangemaakt_op": c.get("detected_at") or _now(),
            },
            "media": [],
            "needs": [],
            "_inbox_reason": "missing_laag1",
        }
        inbox.setdefault("kaarten", []).append(new_card)
        added += 1

    inbox.setdefault("metadata", {})["last_v1_drift_sync"] = _now()
    inbox["metadata"]["last_v1_drift_sync_added"] = added
    inbox["card_count"] = len(inbox["kaarten"])
    save_json(inbox_f, inbox)

    return {
        "success": True,
        "added": added,
        "skipped_sentence": skipped_sentence,
        "skipped_already_v2": skipped_already_v2,
        "skipped_no_begrip": skipped_no_begrip,
        "sample_added": [c["begrip"] for c in candidates[:20]],
    }
