"""
Knowledge Scan Service (v4_005)

Spark scant zijn eigen kennisbank en haalt nieuwe onderwerpen op:
- Loopt door alle ws5-velden (Wie/Wat/Waar/Wanneer/Waarom/Hoe) van elke kaart
- Loopt door alle tags
- Extract meaningful words die nog GEEN snap hebben
- Maakt nieuwe draft-snaps voor die woorden (auto-generated tag)

Bedoeld als 'leer-zelf-uit-jezelf' commando — gestart via chat:
  "scan alle knowledge kaarten op onderwerpen"

Veiligheid:
- max_create cap voorkomt ontploffing
- Stopwoorden filter
- Graph auto-sync gebeurt achter de schermen (per snap)
"""
from pathlib import Path
import re
import uuid
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json
from .snap_service import STOPWOORDEN

KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"


def _extract_words(text: str):
    """Haal betekenisvolle woorden uit een tekst (lowercase, geen stopwoorden, min 3 chars)."""
    if not text or not isinstance(text, str):
        return []
    words = re.findall(r'\b[a-zA-Zéèêëïüöà]+\b', text.lower())
    return [w for w in words if w not in STOPWOORDEN and len(w) > 2]


def scan_for_new_subjects(user_naam: str = "Spark", max_create: int = 100):
    """
    Scan alle ws5-velden + tags van alle entries. Maak nieuwe draft-snaps voor
    onbekende woorden. Return rapport-dict.
    """
    data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
    entries = data.get("knowledge_entries", [])

    # Bestaande begrippen-index
    existing = set()
    for e in entries:
        b = (e.get("begrip") or "").lower().strip()
        if b:
            existing.add(b)

    # Verzamel kandidaat-woorden met bron-tracking
    candidates = {}  # word -> {sources: set, parent_begrippen: set}
    ws5_fields = ("wie", "wat", "wanneer", "waar", "waarom", "hoe")

    for e in entries:
        parent = (e.get("begrip") or "").strip()
        ws5 = e.get("ws5") or {}
        # Per veld
        for field in ws5_fields:
            txt = ws5.get(field)
            if not (txt and isinstance(txt, str)):
                continue
            for w in _extract_words(txt):
                if w in existing:
                    continue
                if w not in candidates:
                    candidates[w] = {"sources": set(), "parent_begrippen": set()}
                candidates[w]["sources"].add(f"ws5.{field}")
                candidates[w]["parent_begrippen"].add(parent)
        # Tags ook scannen
        for tag in (e.get("tags") or []):
            if not isinstance(tag, str):
                continue
            for w in _extract_words(tag):
                if w in existing:
                    continue
                if w not in candidates:
                    candidates[w] = {"sources": set(), "parent_begrippen": set()}
                candidates[w]["sources"].add("tag")
                candidates[w]["parent_begrippen"].add(parent)

    # Sorteer op meeste bronnen (= hoogste signaal) en cap op max_create
    ranked = sorted(
        candidates.items(),
        key=lambda x: (-len(x[1]["sources"]), -len(x[1]["parent_begrippen"]), x[0])
    )
    to_create = ranked[:max_create]

    # Maak snaps aan (zonder duplicate check — die deden we al)
    created_entries = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for word, info in to_create:
        sample_parent = next(iter(info["parent_begrippen"]), "")
        entry = {
            "id": f"snap-{uuid.uuid4().hex[:8]}",
            "begrip": word,
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
            "tags": ["knowledge-snap", "auto-generated", "scan-discovered"],
            "bron": f"scan-from-existing-cards (bron: {sample_parent[:50]})",
            "detected_by": user_naam,
            "detected_at": now_iso,
            "status": "draft",
            "belangrijkheid": 2,
            "usage_count": 0,
            "topic": "",
            "snap_context": f"Gevonden in {len(info['parent_begrippen'])} kaart(en) via {', '.join(sorted(info['sources']))}",
            "metadata": {
                "created_at": now_iso,
                "created_via": "knowledge_scan",
                "is_sentence": False,
                "source_count": len(info["sources"]),
                "source_card_count": len(info["parent_begrippen"]),
            },
        }
        entries.append(entry)
        created_entries.append(entry)

    if created_entries:
        save_json(KNOWLEDGE_FILE, {"knowledge_entries": entries})
        # Graph sync per nieuwe node
        try:
            from modules.graph.sync_service import upsert_node_from_entry
            for e in created_entries:
                upsert_node_from_entry(e)
        except Exception as ex:
            print(f"[scan] graph sync warning: {ex}")

    return {
        "scanned_cards": len(entries) - len(created_entries),
        "candidates_found": len(candidates),
        "new_snaps_created": len(created_entries),
        "sample_words": [e["begrip"] for e in created_entries[:10]],
        "max_create_cap": max_create,
        "capped": len(candidates) > max_create,
    }


# ---- Trigger-detectie ----

SCAN_TRIGGERS = [
    "scan alle knowledge kaarten op onderwerpen",
    "scan alle kaarten op onderwerpen",
    "scan kennis op onderwerpen",
    "scan onderwerpen",
    "spark scan onderwerpen",
    "scan kennisbank op onderwerpen",
    "scan kaarten",
    "scan alle knowledge",
]


def detect_scan_command(text: str) -> bool:
    """Detecteer of user het scan-commando uitspreekt."""
    text_lower = text.lower().strip().rstrip(".!?")
    return any(t in text_lower for t in SCAN_TRIGGERS)
