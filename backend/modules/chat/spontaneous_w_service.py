"""
Spontaneous W-Field Extractor (v4_007)

Wanneer user in een vrije zin een Wie/Wanneer/Waar noemt zonder dat Spark
de vraag stelde, vul stilletjes de lege ws5-velden van de actieve snap aan.

Veiligheidsregels (alle 4 moeten kloppen, anders gebeurt er niks):
1. Er moet een 'last_entry_id' in session_state staan (binnen 10 min)
2. Die snap moet nog tag 'auto-generated' hebben (= niet door admin goedgekeurd)
3. Alleen LEGE ws5-velden worden gevuld (geen overschrijven)
4. Alleen 'wie', 'wanneer', 'waar' — niet waarom/hoe/wat (te subjectief)

Patronen:
- when: gisteren/morgen/maandag/dinsdag/.. + 'X uur' + datum
- where: 'in/op/bij/naar/te' + Hoofdletterwoord
- who:   'met (mijn) X', 'bij mijn X', namen uit persoonskaarten
"""
from pathlib import Path
import re
from datetime import datetime
from modules.core.storage import load_json, save_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "learned_knowledge" / "knowledge_base.json"  # V1 legacy
KBV2_DIR = DATA_DIR / "knowledge" / "v2"
KBV2_LADES = ["doen", "weten", "voelen", "spreken"]


def _find_entry_in_kbv2(entry_id: str):
    """v6_v2_first_001 — vind kaart in V2 lades + inbox. Return (kaart, lade_naam) of (None, None)."""
    for lade in KBV2_LADES + ["inbox"]:
        fname = "knowledge_inbox" if lade == "inbox" else f"knowledge_v2_{lade}"
        d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
        for k in d.get("kaarten", []) or []:
            if k.get("id") == entry_id:
                return k, lade
    return None, None


def _save_lade(lade: str, kaarten: list):
    fname = "knowledge_inbox" if lade == "inbox" else f"knowledge_v2_{lade}"
    save_json(KBV2_DIR / f"{fname}.json", {"kaarten": kaarten})

DAGEN_NL = {
    "maandag", "dinsdag", "woensdag", "donderdag",
    "vrijdag", "zaterdag", "zondag",
}
RELATIVE_TIME = {
    "vandaag", "morgen", "overmorgen", "gisteren", "eergisteren",
    "vannacht", "vanavond", "vanmorgen", "vanmiddag",
}
LOC_PREPS = ("in", "op", "bij", "naar", "te")

# Familie/relatie-woorden voor 'bij mijn X' detectie
FAMILY_WORDS = {
    "moeder", "vader", "zus", "broer", "oma", "opa", "tante", "oom",
    "buurman", "buurvrouw", "vriend", "vriendin", "collega", "baas",
    "dokter", "tandarts", "kapper", "buren", "kind", "dochter", "zoon",
    "neef", "nicht", "schoonmoeder", "schoonvader", "schoonzus", "zwager",
}


def _load_persoon_namen():
    """Lijst van bekende persoonsnamen uit Persoonskaarten (voor who-detectie)."""
    try:
        path = DATA_DIR / "personen.json"
        if not path.exists():
            return set()
        data = load_json(path, default={})
        names = set()
        items = data.get("personen") if isinstance(data, dict) else data
        if isinstance(items, list):
            for p in items:
                if isinstance(p, dict):
                    n = (p.get("naam") or p.get("name") or "").strip().lower()
                    if n:
                        names.add(n)
        return names
    except Exception:
        return set()


def extract_w_fields(text: str) -> dict:
    """Extract who/when/where uit een vrije zin. Lege keys = niks gevonden."""
    result = {}
    text_lower = text.lower()

    # WHEN — relatieve woorden
    for w in RELATIVE_TIME:
        if re.search(rf"\b{w}\b", text_lower):
            result["wanneer"] = w
            break
    if "wanneer" not in result:
        for d in DAGEN_NL:
            if re.search(rf"\b{d}\b", text_lower):
                result["wanneer"] = d
                break
    # Tijd-spec ("om 14:30" of "om 14 uur") als extra
    if "wanneer" in result:
        m = re.search(r"\bom\s+(\d{1,2})(?:[:.](\d{2}))?\s*(?:uur|u\b)?", text_lower)
        if m:
            hour = m.group(1)
            mnt = m.group(2) or "00"
            result["wanneer"] += f" om {hour}:{mnt}"

    # WHERE — preposition + hoofdletterwoord (orig case voor detectie)
    for prep in LOC_PREPS:
        m = re.search(
            rf"\b{prep}\s+(?:de\s+|het\s+|een\s+)?([A-Z][a-zéèêëïüöà]+(?:\s+[A-Z][a-zéèêëïüöà]+)?)",
            text,
        )
        if m:
            result["waar"] = m.group(1).strip()
            break

    # WHO — 'met mijn X' / 'bij mijn X' met familie-woord
    m = re.search(r"\b(?:met|bij)\s+mijn\s+([a-zéèêëïüöà]+)", text_lower)
    if m and m.group(1) in FAMILY_WORDS:
        result["wie"] = f"mijn {m.group(1)}"
    else:
        # 'met X' waarbij X een bekende persoonsnaam is
        namen = _load_persoon_namen()
        if namen:
            m = re.search(r"\b(?:met|bij|samen met)\s+([A-Z][a-zéèêëïüöà]+)", text)
            if m and m.group(1).lower() in namen:
                result["wie"] = m.group(1)

    return result


def _is_card_unapproved(entry: dict) -> bool:
    """Kaart == 'nog niet goedgekeurd' als 'auto-generated' tag aanwezig is."""
    tags = entry.get("tags") or []
    return "auto-generated" in tags


def apply_to_active_card(last_entry_id: str, fields: dict) -> dict:
    """
    Vul lege ws5-velden van de actieve snap, maar alleen als die nog
    auto-generated is. Return dict van velden die echt gevuld zijn.
    """
    if not last_entry_id or not fields:
        return {}
    # v6_v2_first_001 — V2 is bron
    target, lade = _find_entry_in_kbv2(last_entry_id)
    if not target:
        return {}
    if not _is_card_unapproved(target):
        return {}
    ws5 = target.get("ws5") or {}
    filled = {}
    for field in ("who", "when", "where"):
        val = fields.get(field)
        if val and not (ws5.get(field) or "").strip():
            ws5[field] = val
            filled[field] = val
    if filled:
        target["ws5"] = ws5
        tags = target.get("tags") or []
        if "spontaan-verrijkt" not in tags:
            tags.append("spontaan-verrijkt")
        target["tags"] = tags
        # Herlees alle kaarten van die lade, vervang, schrijf
        fname = "knowledge_inbox" if lade == "inbox" else f"knowledge_v2_{lade}"
        d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
        kaarten = d.get("kaarten", [])
        for i, k in enumerate(kaarten):
            if k.get("id") == last_entry_id:
                kaarten[i] = target
                break
        _save_lade(lade, kaarten)
    return filled


def build_hint(filled: dict) -> str:
    """Bouw vriendelijke terloopse hint over wat genoteerd is."""
    if not filled:
        return ""
    parts = []
    if "wanneer" in filled:
        parts.append(f"wanneer: {filled['wanneer']}")
    if "waar" in filled:
        parts.append(f"waar: {filled['waar']}")
    if "wie" in filled:
        parts.append(f"wie: {filled['wie']}")
    return f"_(terloops genoteerd → {', '.join(parts)})_"
