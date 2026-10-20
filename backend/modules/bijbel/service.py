"""v10_bijbel_semantic_layer_001 — Bijbel service.

Wijsheden, patronen, mentale modellen en ankers.
Many-to-many gekoppeld aan KB-begrippen.
"""
from __future__ import annotations

from modules.core.paths import SPARK_ROOT  # v14_spark_root_001
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json

DATA_PATH = Path(f"{SPARK_ROOT}/backend/data/knowledge/learned_knowledge/unified_bijbel_entries.json")

VALID_TYPES = {"wijsheid", "patroon", "mentaal_model", "anker"}
_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> Dict:
    data = load_json(DATA_PATH, default={"unified_entries": [], "metadata": {}})
    if "unified_entries" not in data:
        data["unified_entries"] = []
    return data


def list_entries(
    entry_type: Optional[str] = None,
    begrip: Optional[str] = None,
) -> List[Dict]:
    """Lijst entries, optioneel gefilterd op type of gerelateerd begrip."""
    data = _load()
    out = data.get("unified_entries", [])
    if entry_type:
        out = [e for e in out if e.get("type") == entry_type]
    if begrip:
        b_lower = begrip.lower().strip()
        out = [
            e for e in out
            if any(b_lower == g.lower() for g in e.get("gerelateerde_begrippen", []))
        ]
    # Nieuwste eerst
    out = sorted(out, key=lambda e: e.get("aangemaakt", ""), reverse=True)
    return out


def get_entry(entry_id: str) -> Optional[Dict]:
    data = _load()
    for e in data.get("unified_entries", []):
        if e.get("id") == entry_id:
            return e
    return None


def add_entry(
    tekst: str,
    entry_type: str,
    gerelateerde_begrippen: Optional[List[str]] = None,
    bron: str = "Willem",
    tags: Optional[List[str]] = None,
    notities: str = "",
) -> Dict:
    """Voeg nieuwe entry toe."""
    tekst = (tekst or "").strip()
    if not tekst:
        return {"success": False, "error": "Tekst is leeg"}
    if entry_type not in VALID_TYPES:
        return {
            "success": False,
            "error": f"Ongeldig type: {entry_type}",
            "valid": sorted(VALID_TYPES),
        }

    # Normaliseer begrippen: strip, unique, capitalise first letter
    begrippen = []
    if gerelateerde_begrippen:
        seen = set()
        for b in gerelateerde_begrippen:
            b = (b or "").strip()
            if not b or b.lower() in seen:
                continue
            seen.add(b.lower())
            begrippen.append(b[:1].upper() + b[1:] if len(b) > 1 else b.upper())

    entry = {
        "id": f"bijbel-{uuid.uuid4().hex[:12]}",
        "type": entry_type,
        "tekst": tekst,
        "gerelateerde_begrippen": begrippen,
        "bron": bron or "Willem",
        "tags": [t.strip().lower() for t in (tags or []) if t.strip()],
        "notities": notities,
        "aangemaakt": _now(),
    }

    with _lock:
        data = _load()
        data["unified_entries"].append(entry)
        save_json(DATA_PATH, data)

    return {"success": True, "action": "created", "entry": entry}


def update_entry(entry_id: str, updates: Dict) -> Dict:
    """Update velden van bestaande entry."""
    allowed = {"tekst", "type", "gerelateerde_begrippen", "bron", "tags", "notities"}
    with _lock:
        data = _load()
        for e in data.get("unified_entries", []):
            if e.get("id") == entry_id:
                for k, v in updates.items():
                    if k not in allowed:
                        continue
                    if k == "type" and v not in VALID_TYPES:
                        return {"success": False, "error": f"Ongeldig type: {v}"}
                    if k == "gerelateerde_begrippen" and isinstance(v, list):
                        seen = set()
                        norm = []
                        for b in v:
                            b = (b or "").strip()
                            if not b or b.lower() in seen:
                                continue
                            seen.add(b.lower())
                            norm.append(b[:1].upper() + b[1:] if len(b) > 1 else b.upper())
                        v = norm
                    e[k] = v
                e["bijgewerkt"] = _now()
                save_json(DATA_PATH, data)
                return {"success": True, "entry": e}
    return {"success": False, "error": f"Entry '{entry_id}' niet gevonden"}


def delete_entry(entry_id: str) -> Dict:
    with _lock:
        data = _load()
        entries = data.get("unified_entries", [])
        new_entries = [e for e in entries if e.get("id") != entry_id]
        if len(new_entries) == len(entries):
            return {"success": False, "error": f"Entry '{entry_id}' niet gevonden"}
        data["unified_entries"] = new_entries
        save_json(DATA_PATH, data)
    return {"success": True, "verwijderd": entry_id}


def search_entries(query: str, max_results: int = 10) -> List[Dict]:
    """Zoek in tekst + gerelateerde_begrippen + tags."""
    if not query:
        return []
    q = query.lower().strip()
    data = _load()
    hits = []
    for e in data.get("unified_entries", []):
        score = 0
        tekst = (e.get("tekst") or "").lower()
        if q in tekst:
            score = 80 if tekst.startswith(q) else 60
        for b in e.get("gerelateerde_begrippen", []):
            if q == b.lower():
                score = max(score, 100)
            elif q in b.lower():
                score = max(score, 70)
        for t in e.get("tags", []):
            if q in (t or "").lower():
                score = max(score, 40)
        if score > 0:
            hits.append((score, e))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:max_results]]


def stats() -> Dict:
    """Aantallen per type + top begrippen."""
    data = _load()
    entries = data.get("unified_entries", [])
    per_type = {t: 0 for t in VALID_TYPES}
    begrip_counts: Dict[str, int] = {}
    for e in entries:
        t = e.get("type", "wijsheid")
        per_type[t] = per_type.get(t, 0) + 1
        for b in e.get("gerelateerde_begrippen", []):
            begrip_counts[b] = begrip_counts.get(b, 0) + 1
    top_begrippen = sorted(begrip_counts.items(), key=lambda x: -x[1])[:15]
    return {
        "totaal": len(entries),
        "per_type": per_type,
        "top_begrippen": [{"begrip": b, "count": c} for b, c in top_begrippen],
    }
