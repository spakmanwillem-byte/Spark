"""
Knowledge Base v2 Service (v5_kbv2_001)
========================================
Read/write toegang tot de 4 lades + inbox + index van KB v2.

Architectuur (zie ARCHITECTURE.md → Laag 3: Geheugen):

  knowledge_v2_voelen.json     🌸  emotie/verbinding
  knowledge_v2_spreken.json    💬  taal/dialoog
  knowledge_v2_weten.json      🧠  kennis/systeem
  knowledge_v2_doen.json       🎭  gedrag/actie
  knowledge_inbox.json         📥  onbeantwoord/tie/no-match
  knowledge_index.json         🗂️  begrip → {lade, kaart_id, has_lagen}
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json
from modules.core.spark_logger import traced, log_event

V2_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"

LADES = ["voelen", "spreken", "weten", "doen"]

LADE_META = {
    "voelen": {"icon": "🌸", "naam": "Voelen", "stroom": "Emotie & Verbinding"},
    "spreken": {"icon": "💬", "naam": "Spreken", "stroom": "Communicatie & Taal"},
    "weten": {"icon": "🧠", "naam": "Weten", "stroom": "Systeem & Kennis"},
    "doen": {"icon": "🎭", "naam": "Doen", "stroom": "Gedrag & Actie"},
}

_lock = threading.Lock()


def _lade_path(lade: str) -> Path:
    return V2_DIR / f"knowledge_v2_{lade}.json"


def _inbox_path() -> Path:
    return V2_DIR / "knowledge_inbox.json"


def _index_path() -> Path:
    return V2_DIR / "knowledge_index.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_needs(card: Dict) -> list:
    """Wat mist deze kaart nog? Gebruikt door UI-checklist."""
    needs = []
    lagen = card.get("lagen") or {}
    if not (lagen.get("laag1") or "").strip():
        needs.append("laag1")
    if not any((card.get("ws5") or {}).values()):
        needs.append("ws5")
    media = card.get("media") or {}
    if not media.get("voice_url"):
        needs.append("voice")
    if not (media.get("image_urls") or []):
        needs.append("image")
    return needs


# ---------------------------------------------------------------------------
# Read API
# ---------------------------------------------------------------------------

def get_stats() -> Dict:
    """Snelle stats over alle 4 lades + inbox."""
    stats = {"lades": {}, "inbox_count": 0, "total": 0}
    for lade in LADES:
        d = load_json(_lade_path(lade), default={"kaarten": []})
        n = len(d.get("kaarten", []))
        stats["lades"][lade] = {
            **LADE_META[lade],
            "count": n,
        }
        stats["total"] += n
    inbox = load_json(_inbox_path(), default={"kaarten": []})
    stats["inbox_count"] = len(inbox.get("kaarten", []))
    stats["total"] += stats["inbox_count"]
    return stats


def list_lade(lade: str, limit: int = 50, offset: int = 0, search: str = "") -> Dict:
    """Lijst kaarten in 1 lade. Paged + optioneel zoekfilter op 'begrip'."""
    if lade not in LADES:
        return {"error": f"Onbekende lade '{lade}'"}
    data = load_json(_lade_path(lade), default={"kaarten": []})
    kaarten = data.get("kaarten", [])
    if search:
        s = search.lower().strip()
        kaarten = [k for k in kaarten if s in (k.get("begrip", "") or "").lower()]
    total = len(kaarten)
    # Sorteer alfabetisch op begrip
    kaarten = sorted(kaarten, key=lambda k: (k.get("begrip") or "").lower())
    return {
        "lade": lade,
        **LADE_META[lade],
        "total": total,
        "offset": offset,
        "limit": limit,
        "kaarten": kaarten[offset:offset + limit],
    }


def list_inbox(limit: int = 50, offset: int = 0, reason: str = "", search: str = "") -> Dict:
    """Lijst onbeantwoorde kaarten met optionele filter op _inbox_reason."""
    data = load_json(_inbox_path(), default={"kaarten": []})
    kaarten = data.get("kaarten", [])
    if reason:
        kaarten = [k for k in kaarten if k.get("_inbox_reason") == reason]
    if search:
        s = search.lower().strip()
        kaarten = [k for k in kaarten if s in (k.get("begrip", "") or "").lower()]
    total = len(kaarten)
    # Sorteer: missing_laag1 (heeft niets) eerst onderaan, ties/no_match boven
    priority = {"tag_tie": 0, "no_match": 1, "missing_laag1": 2}
    kaarten = sorted(
        kaarten,
        key=lambda k: (priority.get(k.get("_inbox_reason", ""), 9), (k.get("begrip") or "").lower())
    )
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "kaarten": kaarten[offset:offset + limit],
        "redenen": _count_reasons(data.get("kaarten", [])),
    }


def _count_reasons(cards: List[Dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for c in cards:
        r = c.get("_inbox_reason") or "onbekend"
        out[r] = out.get(r, 0) + 1
    return out


def find_by_begrip(begrip: str) -> Optional[Dict]:
    """Snelle lookup via index. Returnt kaart + lade-info of None."""
    idx = load_json(_index_path(), default={"entries": {}})
    entries = idx.get("entries", {})
    e = entries.get(begrip.lower().strip())
    if not e:
        return None
    lade = e.get("lade")
    kaart_id = e.get("kaart_id")
    if lade:
        bucket = load_json(_lade_path(lade), default={"kaarten": []})
    else:
        bucket = load_json(_inbox_path(), default={"kaarten": []})
    for k in bucket.get("kaarten", []):
        if k.get("id") == kaart_id:
            return {"kaart": k, "lade": lade, "found_in": "lade" if lade else "inbox"}
    return None


def audit() -> Dict:
    """Self-audit: scan v2 op kaarten met lege lagen, ontbrekende footnote, etc.
    Geïnspireerd op v1's AuditService — pure heuristic, geen AI."""
    findings = {
        "empty_laag1": [],
        "missing_footnote": [],
        "low_confidence": [],
        "no_tags": [],
        "inbox_ties": 0,
        "inbox_no_match": 0,
        "inbox_missing_laag1": 0,
    }
    for lade in LADES:
        d = load_json(_lade_path(lade), default={"kaarten": []})
        for k in d.get("kaarten", []):
            lagen = k.get("lagen") or {}
            if not (lagen.get("laag1") or "").strip():
                findings["empty_laag1"].append({"id": k["id"], "begrip": k["begrip"], "lade": lade})
            if not k.get("footnote"):
                findings["missing_footnote"].append({"id": k["id"], "begrip": k["begrip"], "lade": lade})
            elif (k.get("footnote", {}).get("vertrouwen") or 0) < 0.5:
                findings["low_confidence"].append({"id": k["id"], "begrip": k["begrip"], "lade": lade,
                                                    "vertrouwen": k["footnote"]["vertrouwen"]})
            if not k.get("tags"):
                findings["no_tags"].append({"id": k["id"], "begrip": k["begrip"], "lade": lade})

    inbox = load_json(_inbox_path(), default={"kaarten": []})
    for k in inbox.get("kaarten", []):
        r = k.get("_inbox_reason")
        if r == "tag_tie":
            findings["inbox_ties"] += 1
        elif r == "no_match":
            findings["inbox_no_match"] += 1
        elif r == "missing_laag1":
            findings["inbox_missing_laag1"] += 1

    summary = {
        "empty_laag1_count": len(findings["empty_laag1"]),
        "missing_footnote_count": len(findings["missing_footnote"]),
        "low_confidence_count": len(findings["low_confidence"]),
        "no_tags_count": len(findings["no_tags"]),
        "inbox_ties": findings["inbox_ties"],
        "inbox_no_match": findings["inbox_no_match"],
        "inbox_missing_laag1": findings["inbox_missing_laag1"],
    }
    log_event("kbv2", "audit", intent="self-audit kb v2", detail=summary)
    # Beperk findings-lijsten tot top 50 voor UI
    for k in ("empty_laag1", "missing_footnote", "low_confidence", "no_tags"):
        findings[k] = findings[k][:50]
    return {"summary": summary, "findings": findings, "audited_at": _now()}


# ---------------------------------------------------------------------------
# Write API
# ---------------------------------------------------------------------------

@traced(intent="kaart uit inbox in lade plaatsen", module="kbv2")
def classify_card(card_id: str, lade: str, updates: Optional[Dict] = None,
                  user_id: str = "user-000") -> Dict:
    """Verplaats kaart van Inbox naar gekozen lade. Optioneel met edits aan lagen/ws5.
    Werkt index bij. Idempotent als kaart al in lade staat.
    """
    if lade not in LADES:
        return {"success": False, "message": f"Onbekende lade '{lade}'"}

    with _lock:
        inbox = load_json(_inbox_path(), default={"kaarten": []})
        lade_data = load_json(_lade_path(lade), default={"kaarten": []})
        idx = load_json(_index_path(), default={"entries": {}})

        # Vind kaart in inbox
        target_idx = None
        for i, k in enumerate(inbox.get("kaarten", [])):
            if k.get("id") == card_id:
                target_idx = i
                break
        if target_idx is None:
            # Misschien staat hij al in een lade?
            for L in LADES:
                ld = load_json(_lade_path(L), default={"kaarten": []})
                for k in ld.get("kaarten", []):
                    if k.get("id") == card_id:
                        return {"success": False, "message": f"Kaart staat al in lade '{L}'"}
            return {"success": False, "message": f"Kaart '{card_id}' niet gevonden"}

        card = inbox["kaarten"].pop(target_idx)
        card["lade"] = lade
        # Verwijder migratie-meta
        card.pop("_inbox_reason", None)
        card.pop("_classifier_scores", None)
        # Apply updates aan lagen / ws5 / tags
        if updates:
            if "lagen" in updates:
                card["lagen"] = {**(card.get("lagen") or {}), **(updates["lagen"] or {})}
            if "ws5" in updates:
                card["ws5"] = {**(card.get("ws5") or {}), **(updates["ws5"] or {})}
            if "tags" in updates and isinstance(updates["tags"], list):
                card["tags"] = updates["tags"]
        # Footnote-update
        fn = card.get("footnote") or {}
        fn["ingedeeld_door"] = user_id
        fn["ingedeeld_op"] = _now()
        # Recompute confidence based on filled lagen
        lagen_filled = sum(1 for v in (card.get("lagen") or {}).values() if (v or "").strip())
        fn["vertrouwen"] = max(fn.get("vertrouwen", 0.5), round(0.5 + 0.1 * lagen_filled, 2))
        card["footnote"] = fn
        # v5_kbv2_media_001 — needs-checklist bijwerken
        card.setdefault("media", {"voice_url": None, "voice_transcript": None, "image_urls": []})
        card["needs"] = _compute_needs(card)

        # Schrijf weg
        lade_data.setdefault("kaarten", []).append(card)
        lade_data["metadata"] = lade_data.get("metadata") or {}
        lade_data["metadata"]["card_count"] = len(lade_data["kaarten"])
        lade_data["metadata"]["last_updated"] = _now()

        save_json(_lade_path(lade), lade_data)
        save_json(_inbox_path(), inbox)

        # Index update
        idx.setdefault("entries", {})[(card.get("begrip") or "").lower().strip()] = {
            "kaart_id": card["id"],
            "lade": lade,
            "has_lagen": [k for k, v in (card.get("lagen") or {}).items() if v],
            "last_updated": _now(),
        }
        save_json(_index_path(), idx)

    return {"success": True, "kaart": card, "lade": lade}


@traced(intent="bestaande kaart in lade bewerken", module="kbv2")
def edit_card(card_id: str, lade: str, updates: Dict, user_id: str = "user-000") -> Dict:
    """Update lagen / ws5 / tags / begrip van een kaart die al in een lade staat."""
    if lade not in LADES:
        return {"success": False, "message": f"Onbekende lade '{lade}'"}
    with _lock:
        data = load_json(_lade_path(lade), default={"kaarten": []})
        for k in data.get("kaarten", []):
            if k.get("id") == card_id:
                if "lagen" in updates:
                    k["lagen"] = {**(k.get("lagen") or {}), **(updates["lagen"] or {})}
                if "ws5" in updates:
                    k["ws5"] = {**(k.get("ws5") or {}), **(updates["ws5"] or {})}
                if "tags" in updates and isinstance(updates["tags"], list):
                    k["tags"] = updates["tags"]
                if "begrip" in updates and updates["begrip"]:
                    k["begrip"] = updates["begrip"]
                # v5_kbv2_media_001 — media-updates (voice + images)
                if "media" in updates and isinstance(updates["media"], dict):
                    k["media"] = {**(k.get("media") or {}), **updates["media"]}
                fn = k.get("footnote") or {}
                fn["laatst_bewerkt_door"] = user_id
                fn["laatst_bewerkt_op"] = _now()
                k["footnote"] = fn
                k.setdefault("media", {"voice_url": None, "voice_transcript": None, "image_urls": []})
                k["needs"] = _compute_needs(k)
                save_json(_lade_path(lade), data)
                # Index bijwerken
                idx = load_json(_index_path(), default={"entries": {}})
                idx.setdefault("entries", {})[k["begrip"].lower().strip()] = {
                    "kaart_id": k["id"], "lade": lade,
                    "has_lagen": [kk for kk, vv in k["lagen"].items() if vv],
                    "last_updated": _now(),
                }
                save_json(_index_path(), idx)
                return {"success": True, "kaart": k}
    return {"success": False, "message": f"Kaart '{card_id}' niet gevonden in lade '{lade}'"}


@traced(intent="nieuwe kaart toevoegen aan inbox", module="kbv2")
def add_to_inbox(begrip: str, source: str = "user", user_id: str = "user-000") -> Dict:
    """Maak een lege kaart in de inbox (bv. wanneer Spark een onbekend woord tegenkomt).
    Idempotent: als 'begrip' al ergens bestaat, return existing."""
    if not begrip or not begrip.strip():
        return {"success": False, "message": "Leeg begrip"}
    existing = find_by_begrip(begrip)
    if existing:
        return {"success": True, "kaart": existing["kaart"], "existing": True, "lade": existing["lade"]}
    with _lock:
        inbox = load_json(_inbox_path(), default={"kaarten": []})
        new_card = {
            "id": f"kbv2-{uuid.uuid4().hex[:8]}",
            "begrip": begrip.strip(),
            "lade": None,
            "status": "draft",
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {},
            "tags": [],
            "verbanden": [],
            "footnote": {
                "bron": source,
                "ingedeeld_door": None,
                "ingedeeld_op": None,
                "vorige_versie_v1": None,
                "vertrouwen": 0.3,
                "aangemaakt_door": user_id,
                "aangemaakt_op": _now(),
            },
            "_inbox_reason": "missing_laag1",
        }
        inbox.setdefault("kaarten", []).append(new_card)
        save_json(_inbox_path(), inbox)
        # Index ook
        idx = load_json(_index_path(), default={"entries": {}})
        idx.setdefault("entries", {})[begrip.lower().strip()] = {
            "kaart_id": new_card["id"], "lade": None,
            "has_lagen": [], "last_updated": _now(),
        }
        save_json(_index_path(), idx)
    return {"success": True, "kaart": new_card, "existing": False}


# ---------------------------------------------------------------------------
# Graceful Fallback (#DeWillem principe)
# ---------------------------------------------------------------------------

def graceful_fallback(begrip: str) -> Optional[Dict]:
    """#DeWillem: stap-terug-en-geef-context i.p.v. 'ik weet het niet'.
    
    Strategie:
      1. Direct hit via index? → return kaart
      2. Geen direct hit → check buurkaarten (kaarten met overlappende tags) per lade
      3. Geen buurkaarten → return None (caller doet dan fallback-prompt
         "Ik ken nog geen X. Wil je dat ik dit leer?")
    """
    direct = find_by_begrip(begrip)
    if direct:
        return {"type": "direct", **direct}
    # Tokenize begrip-zoektermen
    tokens = {t.strip().lower() for t in begrip.replace(",", " ").split() if t.strip()}
    if not tokens:
        return None
    best: Optional[Dict] = None
    best_score = 0
    for lade in LADES:
        d = load_json(_lade_path(lade), default={"kaarten": []})
        for k in d.get("kaarten", []):
            tags = {(t or "").lower() for t in (k.get("tags") or [])}
            score = len(tokens & tags)
            if score > best_score:
                best = {"type": "neighbor", "kaart": k, "lade": lade, "overlap": score}
                best_score = score
    return best
