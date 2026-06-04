"""
v6_kbv2_text_importer_001 — Parse rijke txt-dumps van Spark-kaarten.

Ondersteunde formaat (flexibel):
    Begrip                           ← single line of "Title" met optionele lowercase regel boven
    
    Laag 1
    [tekst]
    
    Laag 2
    [tekst]
    
    Laag 3
    [tekst]
    
    Laag 4
    [tekst]
    
    5W (...) of "5W" alleen
    
    Wie / Wat / Wanneer / Waar / Waarom / Hoe
    [waarde]
    OF inline: "Wie: ..."
    
    Tags
    tag1, tag2, ...
    
    Lade
    🎭 Doen   OF   doen   OF  "🎭 Doen"
    
    Emotie
    Blij | Boos | Bang | Bedroefd | Neutraal
    
    Kernzin (optioneel — voegt toe aan laag1 als ontbreekt)
    [tekst]

Output: lijst van card-dicts klaar voor toevoegen aan KB v1 + v2.
"""
import re
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone

LADE_EMOJI_MAP = {
    "🎭": "doen", "doen": "doen", "🎭 doen": "doen",
    "🧠": "weten", "weten": "weten", "🧠 weten": "weten",
    "🌸": "voelen", "voelen": "voelen", "🌸 voelen": "voelen",
    "💬": "spreken", "spreken": "spreken", "💬 spreken": "spreken",
}


def _normalize_lade(s: str) -> Optional[str]:
    if not s:
        return None
    k = s.strip().lower()
    for prefix, val in LADE_EMOJI_MAP.items():
        if k.startswith(prefix.lower()) or k == prefix.lower():
            return val
    return None


def _norm_emotion(s: str) -> str:
    s = (s or "").strip().lower()
    return {"blij": "blij", "boos": "boos", "bang": "bang",
            "bedroefd": "bedroefd", "verdrietig": "bedroefd",
            "neutraal": "neutraal", "rustig": "neutraal"}.get(s, "neutraal")


# ===== Block-detection =====
# We splitsen het document in **kaart-blokken**. Een nieuw blok begint bij een
# begrip-titel: een korte regel (1-3 woorden) gevolgd door óf een herhaling
# (lowercase → Capitalized) óf direct "Laag 1".
_LAAG_RX = re.compile(r"^\s*Laag\s*([1-4])\b\s*(?:[—:-].*)?$", re.IGNORECASE | re.MULTILINE)
_LADE_HDR_RX = re.compile(r"^\s*Lade\s*$", re.IGNORECASE | re.MULTILINE)
_TAGS_HDR_RX = re.compile(r"^\s*Tags\s*$", re.IGNORECASE | re.MULTILINE)
_5W_HDR_RX = re.compile(r"^\s*5W(?:\s*\(.*?\))?\s*$", re.IGNORECASE | re.MULTILINE)
_EMOTIE_HDR_RX = re.compile(r"^\s*Emotie\s*$", re.IGNORECASE | re.MULTILINE)
_KERNZIN_HDR_RX = re.compile(r"^\s*Kernzin\s*$", re.IGNORECASE | re.MULTILINE)


def split_into_blocks(text: str) -> List[str]:
    """Vind alle kaart-blokken in de tekst.

    Strategie: zoek alle 'Laag 1' posities, neem de tekst tussen die en de
    volgende 'Laag 1' (of einde) als één blok. Dan extracteren we het begrip
    uit de regels vóór 'Laag 1'.
    """
    laag1_positions = [m.start() for m in re.finditer(r"^\s*Laag\s*1\b", text, re.IGNORECASE | re.MULTILINE)]
    blocks = []
    # Voeg start van tekst toe als eerste 'context'-start
    for i, pos in enumerate(laag1_positions):
        # Block start: terug naar de header vóór dit blok
        if i == 0:
            block_start = 0
        else:
            # Begin op een redelijke afstand vóór "Laag 1" — pak alles tussen vorig blok-eind
            # We doen dit door eerst de blocks-by-content af te bouwen.
            prev_end = laag1_positions[i - 1]
            # Loop terug in de tekst: vind eerste lege regel ná `prev_end`
            block_start = text.rfind("\n\n", prev_end, pos)
            if block_start == -1:
                block_start = prev_end
            block_start += 1
        block_end = laag1_positions[i + 1] if i + 1 < len(laag1_positions) else len(text)
        # Maar eindig bij volgende 'begrip-header'-marker als die nog dichter is
        blocks.append(text[block_start:block_end].strip())
    return blocks


def _extract_begrip(pre_laag_text: str) -> Optional[str]:
    """Vind de begrip-titel in de regels vóór 'Laag 1'."""
    # Strategie: neem laatste niet-lege regel die geen header is en niet "Laag 1" zelf,
    # filter typische sub-headers eruit
    lines = [ln.strip() for ln in pre_laag_text.strip().splitlines() if ln.strip()]
    # Bekende headers die GEEN begrip zijn
    skip = {"5w", "5w (wie/wat/wanneer/waar/waarom/hoe)", "tags", "lade", "emotie",
            "kernzin", "laag 1", "laag 2", "laag 3", "laag 4", "laag 1 — kort antwoord / definitie",
            "wie", "wat", "wanneer", "waar", "waarom", "hoe"}
    candidates = [ln for ln in lines if ln.lower() not in skip]
    if not candidates:
        return None
    # Begrip is de laatste candidate vóór Laag 1; vaak is dat een Capitalized
    # of titel-case versie. Skip lowercase doubles ("amusement" gevolgd door "Amusement").
    last = candidates[-1]
    # Als de last lowercase is en de eerste letter zelfde naam-prefix als één eerder die hoofdletter heeft, kies eerst
    if len(candidates) >= 2 and candidates[-1].lower() == candidates[-2].lower():
        last = candidates[-2] if candidates[-2][0].isupper() else candidates[-1]
    # Strip prefixes als "kwetsbaarheden\nKwetsbaarheden" → "Kwetsbaarheden"
    return last.strip().rstrip(":")


def _extract_field(block: str, header_rx: re.Pattern, multi: bool = True) -> Optional[str]:
    """Extract content tussen header-match en volgend blok-header. multi: meerdere regels."""
    m = header_rx.search(block)
    if not m:
        return None
    rest = block[m.end():]
    # Stop bij volgende header (Laag X / 5W / Tags / Lade / Emotie / Wie / Wat etc.)
    next_header = re.search(
        r"^\s*(Laag\s*[1-4]|5W|Tags|Lade|Emotie|Kernzin|Wie|Wat|Wanneer|Waar|Waarom|Hoe)\b",
        rest, re.IGNORECASE | re.MULTILINE
    )
    if next_header:
        content = rest[:next_header.start()]
    else:
        content = rest
    return content.strip() or None


def _extract_5w(block: str) -> Dict[str, str]:
    """Extract Wie/Wat/Wanneer/Waar/Waarom/Hoe. Beide formats: 'Wie: ...' inline OR per regel."""
    out = {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""}
    # Inline format: "Wie: ..." per regel
    for key in out.keys():
        inline = re.search(rf"^\s*{key}\s*:\s*(.+?)$", block, re.IGNORECASE | re.MULTILINE)
        if inline:
            out[key] = inline.group(1).strip()
        else:
            # Block-format: header on one line, content on next lines until next header
            hdr_rx = re.compile(rf"^\s*{key}\s*$", re.IGNORECASE | re.MULTILINE)
            content = _extract_field(block, hdr_rx)
            if content:
                out[key] = content
    return out


def _extract_tags(block: str) -> List[str]:
    content = _extract_field(block, _TAGS_HDR_RX)
    if not content:
        return []
    # Splits op komma, strip, filter lege
    return [t.strip().lower() for t in content.split(",") if t.strip()]


def parse_text_to_cards(text: str) -> List[Dict]:
    """Parse de hele tekst → lijst van card-dicts.

    Output formaat per kaart:
      {"begrip": str, "lade": "doen"|"weten"|"voelen"|"spreken",
       "emotie": "blij"|...,
       "lagen": {"laag1": "...", ...},
       "ws5": {"wie": "...", ...},
       "tags": [...], "kernzin": "..."|None,
       "_raw_block": "..."}
    """
    blocks = split_into_blocks(text)
    cards: List[Dict] = []
    seen_begrip = set()

    for block in blocks:
        # Splits in pre-laag1 (begrip-detection) en rest
        m_laag1 = _LAAG_RX.search(block)
        if not m_laag1:
            continue
        pre = block[:m_laag1.start()]
        begrip = _extract_begrip(pre)
        if not begrip:
            continue
        begrip_lc = begrip.lower().strip()
        if begrip_lc in seen_begrip:
            continue
        seen_begrip.add(begrip_lc)

        # Extract lagen
        lagen = {}
        for i in range(1, 5):
            hdr = re.compile(rf"^\s*Laag\s*{i}\b\s*(?:[—:-].*)?$", re.IGNORECASE | re.MULTILINE)
            c = _extract_field(block, hdr)
            lagen[f"laag{i}"] = c or ""

        # Extract overige velden
        tags = _extract_tags(block)
        # Filter "emotie" en emotie-labels uit tags (die horen apart)
        emotion_words = {"emotie", "blij", "boos", "bang", "bedroefd", "verdrietig", "neutraal", "rustig"}
        clean_tags = [t for t in tags if t not in emotion_words]

        ws5 = _extract_5w(block)
        lade_raw = _extract_field(block, _LADE_HDR_RX)
        lade = _normalize_lade(lade_raw or "")
        emotie_raw = _extract_field(block, _EMOTIE_HDR_RX) or ""
        emotie = _norm_emotion(emotie_raw)
        # v6_text_importer_001 — fallback: detecteer emotie ook uit tags-lijst van origineel
        if emotie == "neutraal":
            emotion_set = {"blij", "boos", "bang", "bedroefd", "verdrietig"}
            for t in tags:
                if t in emotion_set:
                    emotie = _norm_emotion(t)
                    break
        kernzin = _extract_field(block, _KERNZIN_HDR_RX)

        cards.append({
            "begrip": begrip,
            "lade": lade,
            "emotie": emotie,
            "lagen": lagen,
            "ws5": ws5,
            "tags": clean_tags,
            "kernzin": kernzin,
        })

    return cards


# ===== Apply to KB v1 + v2 =====
DATA_DIR = Path(__file__).parent.parent.parent / "data"
KB_V1 = DATA_DIR / "knowledge" / "learned_knowledge" / "knowledge_base.json"
KB_V2 = DATA_DIR / "knowledge" / "v2"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_cards_to_kb(cards: List[Dict], user_id: str = "user-001",
                     overwrite_existing: bool = False) -> Dict:
    """Voeg parsed cards toe aan KB v1 + KB v2. Idempotent (skipt aanwezige met
    gevulde laag1, tenzij overwrite_existing).
    Returns summary."""
    from modules.core.storage import load_json, save_json

    summary = {"parsed": len(cards), "added_v2": 0, "added_v1": 0,
               "updated_v1": 0, "skipped": 0, "errors": [], "details": []}

    # Load V1
    kb1 = load_json(KB_V1, default={"knowledge_entries": []})
    kb1_entries = kb1.get("knowledge_entries", [])
    kb1_by_begrip = {(e.get("begrip") or "").lower().strip(): e for e in kb1_entries if e.get("begrip")}

    # Load V2 per lade
    v2_data = {}
    for lade in ("voelen", "spreken", "weten", "doen"):
        f = KB_V2 / f"knowledge_v2_{lade}.json"
        v2_data[lade] = load_json(f, default={"kaarten": []})

    for c in cards:
        b = c.get("begrip", "").strip()
        b_lc = b.lower()
        lade = c.get("lade") or "weten"
        if lade not in v2_data:
            summary["errors"].append({"begrip": b, "reason": f"onbekende lade '{lade}'"})
            continue

        # Filtering: skip als geen laag1
        if not (c.get("lagen") or {}).get("laag1", "").strip():
            summary["skipped"] += 1
            summary["details"].append({"begrip": b, "reason": "geen laag1"})
            continue

        # --- KB V1 update ---
        v1_existing = kb1_by_begrip.get(b_lc)
        if v1_existing:
            cur_l1 = (v1_existing.get("lagen") or {}).get("laag1", "")
            if not cur_l1 or overwrite_existing:
                v1_existing["lagen"] = c["lagen"]
                v1_existing["ws5"] = c["ws5"]
                # Merge tags
                existing_tags = set(v1_existing.get("tags") or [])
                for t in c["tags"]:
                    existing_tags.add(t)
                v1_existing["tags"] = sorted(existing_tags)
                v1_existing["status"] = "active"
                v1_existing["updated_at"] = _now()
                v1_existing["updated_by"] = user_id
                v1_existing["belangrijkheid"] = max(int(v1_existing.get("belangrijkheid") or 1), 3)
                summary["updated_v1"] += 1
            else:
                summary["skipped"] += 1
                summary["details"].append({"begrip": b, "reason": "v1 al gevuld"})
                continue
        else:
            kb1_entries.append({
                "id": f"kb-{uuid.uuid4().hex[:8]}",
                "begrip": b,
                "status": "active",
                "lagen": c["lagen"],
                "ws5": c["ws5"],
                "tags": c["tags"],
                "topic": "",
                "belangrijkheid": 3,
                "usage_count": 0,
                "detected_by": user_id,
                "created_by": user_id,
                "created_at": _now(),
                "metadata": {"source": "text_importer"},
            })
            summary["added_v1"] += 1

        # --- KB V2 — check binnen alle lades op duplicate ---
        v2_found = None
        v2_found_lade = None
        for lade_key, lade_data in v2_data.items():
            for k in lade_data.get("kaarten", []):
                if (k.get("begrip") or "").lower().strip() == b_lc:
                    v2_found = k
                    v2_found_lade = lade_key
                    break
            if v2_found:
                break

        if v2_found:
            cur_l1 = (v2_found.get("lagen") or {}).get("laag1", "")
            if not cur_l1 or overwrite_existing:
                v2_found["lagen"] = c["lagen"]
                v2_found["ws5"] = c["ws5"]
                existing_tags = set(v2_found.get("tags") or [])
                for t in c["tags"]:
                    existing_tags.add(t)
                v2_found["tags"] = sorted(existing_tags)
                v2_found["status"] = "active"
                v2_found["lade"] = lade
                if c.get("emotie"):
                    v2_found["emotie"] = c["emotie"]
                fn = v2_found.setdefault("footnote", {})
                fn["bron"] = "text_importer"
                fn["updated_at"] = _now()
                # Als de v2 in andere lade staat → verplaats
                if v2_found_lade != lade:
                    v2_data[v2_found_lade]["kaarten"].remove(v2_found)
                    v2_data[lade]["kaarten"].append(v2_found)
                summary["details"].append({"begrip": b, "v2_action": "updated" + (
                    f" + moved to {lade}" if v2_found_lade != lade else "")})
            else:
                summary["details"].append({"begrip": b, "v2_action": "already filled"})
        else:
            new_card = {
                "id": f"kbv2-{uuid.uuid4().hex[:8]}",
                "begrip": b,
                "lade": lade,
                "status": "active",
                "lagen": c["lagen"],
                "ws5": c["ws5"],
                "tags": c["tags"],
                "topic": "",
                "verbanden": [],
                "footnote": {"bron": "text_importer", "ingedeeld_door": user_id,
                             "ingedeeld_op": _now(), "vertrouwen": 1.0,
                             "belangrijkheid": 0.5, "hooks_fired": []},
                "media": [],
                "needs": [],
            }
            if c.get("emotie"):
                new_card["emotie"] = c["emotie"]
            v2_data[lade]["kaarten"].append(new_card)
            summary["added_v2"] += 1

    # Save
    save_json(KB_V1, kb1)
    for lade_key, lade_data in v2_data.items():
        save_json(KB_V2 / f"knowledge_v2_{lade_key}.json", lade_data)

    # Update index
    idx_f = KB_V2 / "knowledge_index.json"
    idx = load_json(idx_f, default={"entries": {}})
    entries = idx.setdefault("entries", {})
    for lade_key, lade_data in v2_data.items():
        for k in lade_data.get("kaarten", []):
            b = (k.get("begrip") or "").lower().strip()
            if b:
                entries[b] = {
                    "kaart_id": k.get("id"), "lade": lade_key,
                    "has_lagen": [kk for kk, vv in (k.get("lagen") or {}).items() if vv],
                    "last_updated": _now(),
                }
    idx["entry_count"] = len(entries)
    save_json(idx_f, idx)

    return summary
