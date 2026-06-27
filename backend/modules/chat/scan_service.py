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

KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"  # V1 legacy
KBV2_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"
KBV2_LADES = ["doen", "weten", "voelen", "spreken"]


def _load_all_kbv2():
    """v6_v2_first_001 — alle V2 kaarten (4 lades + inbox)."""
    out = []
    for fname in [f"knowledge_v2_{l}" for l in KBV2_LADES] + ["knowledge_inbox"]:
        d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
        out.extend(d.get("kaarten", []) or [])
    return out


def _append_to_inbox(new_kaarten: list):
    """Voeg nieuwe kaarten toe aan V2 inbox."""
    inbox_fp = KBV2_DIR / "knowledge_inbox.json"
    inbox = load_json(inbox_fp, default={"kaarten": []})
    inbox.setdefault("kaarten", []).extend(new_kaarten)
    save_json(inbox_fp, inbox)


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
    v6_v2_first_001 — V2 is bron; nieuwe kaarten gaan naar V2 inbox.
    """
    entries = _load_all_kbv2()

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

    # Maak skelet-kaarten in V2-vorm (gaan naar inbox)
    created_entries = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for word, info in to_create:
        sample_parent = next(iter(info["parent_begrippen"]), "")
        entry = {
            "id": f"kbv2-skel-{uuid.uuid4().hex[:8]}",
            "begrip": word,
            "lade": "",  # nog in inbox
            "status": "draft",
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
            "tags": ["knowledge-snap", "auto-generated", "scan-discovered"],
            "topic": "",
            "verbanden": [],
            "media": {},
            "needs": [],
            "footnote": {
                "bron": f"scan-from-existing-cards (bron: {sample_parent[:50]})",
                "ingedeeld_door": user_naam,
                "ingedeeld_op": now_iso,
                "vertrouwen": 0.5,
                "belangrijkheid": 2,
            },
            "metadata": {
                "created_at": now_iso,
                "created_via": "knowledge_scan",
                "source_count": len(info["sources"]),
                "source_card_count": len(info["parent_begrippen"]),
                "snap_context": f"Gevonden in {len(info['parent_begrippen'])} kaart(en) via {', '.join(sorted(info['sources']))}",
            },
        }
        created_entries.append(entry)

    if created_entries:
        _append_to_inbox(created_entries)
        # Graph sync per nieuwe node
        try:
            from modules.graph.sync_service import upsert_node_from_entry
            for e in created_entries:
                upsert_node_from_entry(e)
        except Exception as ex:
            print(f"[scan] graph sync warning: {ex}")

    return {
        "scanned_cards": len(entries),
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
