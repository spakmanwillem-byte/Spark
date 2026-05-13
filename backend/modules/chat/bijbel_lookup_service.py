"""
Bijbel Lookup Service (v4_011) — Spark gebruikt zijn eigen Bijbel/Waarden/Normen
om zelf-reflectieve vragen te beantwoorden.

Voorbeeld:
- User: "waar word je blij van?" → vraagt naar Spark's voorkeur
  → zoek bijbel-items + kernwaarden met tag `blij` (of emotie blij)
  → bouw antwoord uit beschrijving + lagen + voorbeelden

Detect-intents:
- voorkeur_blij/boos/bang/bedroefd/neutraal → "waar word je blij van?"
- missie / visie → "wat is jouw missie/visie?"
- doel / functie → "wat is jouw doel?"
- waarde / norm  → "wat zijn jouw waarden/normen?"
- filosofie / overtuiging / belief / geloof → "waar geloof je in?"
"""
import re
from pathlib import Path
from modules.core.storage import load_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
BIJBEL_FILE = DATA_DIR / "personality" / "spark_bijbel.json"
IDENTITY_FILE = DATA_DIR / "personality" / "spark_identity.json"


# Mapping intent → ( zoektags-prioriteit, antwoord-prefix )
INTENT_DEFINITIONS = {
    "voorkeur_blij":     {"tags": ["blij"],          "prefix": "Waar ik blij van word:"},
    "voorkeur_boos":     {"tags": ["boos"],          "prefix": "Waar ik boos van word:"},
    "voorkeur_bang":     {"tags": ["bang"],          "prefix": "Waar ik bang van word:"},
    "voorkeur_bedroefd": {"tags": ["bedroefd"],      "prefix": "Waar ik verdrietig van word:"},
    "missie":            {"tags": ["missie"],        "prefix": "Mijn missie:"},
    "visie":             {"tags": ["visie"],         "prefix": "Mijn visie:"},
    "doel":              {"tags": ["doel"],          "prefix": "Mijn doel:"},
    "functie":           {"tags": ["functie"],       "prefix": "Mijn functie:"},
    "filosofie":         {"tags": ["filosofie"],     "prefix": "Mijn filosofie:"},
    "geloof":            {"tags": ["geloof", "belief", "overtuiging"], "prefix": "Waar ik in geloof:"},
    "behoefte":          {"tags": ["behoefte", "need"], "prefix": "Wat ik nodig heb:"},
    "waarde":            {"tags": ["waarde"],        "prefix": "Mijn kernwaarden:"},
    "norm":              {"tags": ["norm"],          "prefix": "Mijn normen:"},
}


# Triggers per intent (substring match in user-bericht, lowercased)
INTENT_TRIGGERS = {
    "voorkeur_blij": [
        "waar word je blij van", "wat maakt jou blij", "wat maakt je blij",
        "waar word jij blij van", "wat vind jij leuk", "wat maakt jou gelukkig",
        "wat geeft jou energie",
    ],
    "voorkeur_boos": [
        "waar word je boos van", "wat maakt jou boos", "wat irriteert je",
        "wat maakt je boos",
    ],
    "voorkeur_bang": [
        "waar ben je bang voor", "waar word je bang van", "wat maakt jou bang",
    ],
    "voorkeur_bedroefd": [
        "waar word je verdrietig van", "waar word je bedroefd van",
        "wat maakt jou verdrietig", "wat maakt je verdrietig",
    ],
    "missie": ["wat is je missie", "wat is jouw missie", "wat is spark's missie"],
    "visie": ["wat is je visie", "wat is jouw visie", "wat is spark's visie"],
    "doel": [
        "wat is je doel", "wat is jouw doel", "waarom besta je", "waar ben je voor",
        "wat is je levensdoel",
    ],
    "functie": ["wat is je functie", "wat is jouw functie", "wat is je rol"],
    "filosofie": [
        "wat is je filosofie", "wat is jouw filosofie", "wat is jouw levensvisie",
    ],
    "geloof": [
        "waar geloof je in", "waar geloof jij in", "wat zijn je overtuigingen",
        "waar sta jij voor",
    ],
    "behoefte": ["wat heb je nodig", "wat heb jij nodig", "wat is je behoefte"],
    "waarde": [
        "wat zijn je waarden", "wat zijn jouw waarden", "wat zijn je kernwaarden",
        "wat vind je belangrijk", "wat vind jij belangrijk",
    ],
    "norm": ["wat zijn je normen", "wat zijn jouw normen"],
}


def detect_self_question(text: str):
    """Detecteer of user vraagt naar Spark's eigen voorkeur/missie/etc.
    Geeft intent-naam terug of None."""
    t = (text or "").lower().strip()
    if not t:
        return None
    # Vereisten: er moet een 'jij/je/jouw/spark' referentie in zitten
    has_self_ref = any(r in t for r in (" je ", " jij ", " jouw ", " jou ", "spark"))
    # Of begin/eind van zin met 'je/jij'
    if not has_self_ref:
        if any(t.startswith(r) for r in ("je ", "jij ", "jouw ", "spark")):
            has_self_ref = True
        if any(t.endswith(r) for r in (" je", " jij", " jou")):
            has_self_ref = True
    if not has_self_ref:
        return None
    for intent, triggers in INTENT_TRIGGERS.items():
        for trig in triggers:
            if trig in t:
                return intent
    return None


def _all_items_with_tags():
    """Lever lijst (section_label, item) voor alle bijbel-secties met tags-veld."""
    data = load_json(BIJBEL_FILE, default={})
    out = []
    for section_key, label in (
        ("kernwaarden", "Kernwaarde"),
        ("normen", "Norm"),
        ("bijbel_items", "Bijbel"),
    ):
        for item in data.get(section_key, []) or []:
            if isinstance(item, dict):
                out.append((label, section_key, item))
    return out


def _item_title(section_key: str, item: dict):
    return (item.get("waarde") or item.get("norm") or item.get("naam") or "").strip()


def _item_text(item: dict):
    """Bouw de inhoudelijke tekst van een item: laag1-4 of beschrijving."""
    lagen = item.get("lagen") or {}
    for k in ("laag1", "laag2", "laag3", "laag4"):
        v = (lagen.get(k) or "").strip()
        if v:
            return v
    return (item.get("beschrijving") or "").strip()


def lookup_by_tag(target_tags):
    """Zoek items waarvan tags overlappen met target_tags (case-insensitive,
    `#` wordt genegeerd). Sorteer op belangrijkheid desc."""
    targets = {t.lower().strip().lstrip("#") for t in target_tags}
    hits = []
    for label, section_key, item in _all_items_with_tags():
        tags = {(t or "").lower().strip().lstrip("#") for t in (item.get("tags") or [])}
        if tags & targets:
            hits.append({
                "section": section_key,
                "label": label,
                "title": _item_title(section_key, item),
                "text": _item_text(item),
                "belangrijkheid": item.get("belangrijkheid") or 0,
                "id": item.get("id"),
            })
    hits.sort(key=lambda h: h["belangrijkheid"], reverse=True)
    return hits


def lookup_doelen():
    data = load_json(BIJBEL_FILE, default={})
    return data.get("doelen", []) or []


def lookup_identity_field(field_name: str):
    """Haal veld uit spark_identity.json (doel, persoonlijkheid.filosofie...)."""
    data = load_json(IDENTITY_FILE, default={})
    if "." in field_name:
        parts = field_name.split(".")
        cur = data
        for p in parts:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(p)
        return cur
    return data.get(field_name)


def compose_reply(intent: str, max_items: int = 3):
    """Bouw antwoord voor een self-question intent."""
    defn = INTENT_DEFINITIONS.get(intent)
    if not defn:
        return None
    hits = lookup_by_tag(defn["tags"])

    # Speciale fallbacks per intent
    extra_lines = []
    if intent == "doel" and not hits:
        # Probeer identity.doel + doelen-lijst
        idoel = lookup_identity_field("doel")
        if idoel:
            extra_lines.append(f"- {idoel}")
        for d in lookup_doelen()[:max_items]:
            extra_lines.append(f"- {d}")
    elif intent == "filosofie" and not hits:
        fil = lookup_identity_field("persoonlijkheid.filosofie")
        if fil:
            extra_lines.append(f"- {fil}")
    elif intent == "waarde" and not hits:
        # Alle kernwaarden ongeacht tag
        data = load_json(BIJBEL_FILE, default={})
        for kw in (data.get("kernwaarden") or [])[:max_items]:
            t = (kw.get("waarde") or "").strip()
            b = (kw.get("beschrijving") or "").strip()
            if t or b:
                extra_lines.append(f"- **{t}**: {b}" if t and b else f"- {t or b}")
    elif intent == "norm" and not hits:
        data = load_json(BIJBEL_FILE, default={})
        for n in (data.get("normen") or [])[:max_items]:
            t = (n.get("norm") or "").strip()
            b = (n.get("beschrijving") or "").strip()
            if t or b:
                extra_lines.append(f"- **{t}**: {b}" if t and b else f"- {t or b}")

    parts = [defn["prefix"]]
    if hits:
        for h in hits[:max_items]:
            title = h["title"]
            text = h["text"] or "_(nog geen uitleg ingevuld)_"
            label = h["label"]
            line = f"- **{title}** _({label})_: {text}" if title else f"- {text}"
            parts.append(line)
    if extra_lines:
        parts.extend(extra_lines)

    if len(parts) == 1:
        # Niets gevonden — leg uit dat de Bijbel nog leeg is voor deze intent
        parts.append(
            "_(Mijn Spark Bijbel heeft hier nog geen items voor. "
            "Voeg ze toe via Spark Brain → Normen & Waarden of Spark Bijbel.)_"
        )
    return "\n".join(parts)
