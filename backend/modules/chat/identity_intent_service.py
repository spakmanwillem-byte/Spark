"""
Identity Intent Service (v4_identity_001) — Spark beantwoordt vragen over zichzelf.

Plugt in chat/routes.py vóór de generieke knowledge lookup.
Herkent identity-vragen via regex patterns en bouwt antwoorden uit:
  - spark_identity.json (basis, doel, traits, filosofie)
  - spark_profile.json (uitgebreide biografie + waarden)
  - spark_bijbel.json (kernwaarden + normen)
  - knowledge_base.json (kaarten "Visie", "Core", "Missie (visie)")

Geen wijzigingen aan andere bestanden — leest alleen.
"""
import re
from pathlib import Path
from typing import Optional, Dict, List

from modules.core.storage import load_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
IDENTITY_FILE = DATA_ROOT / "personality" / "spark_identity.json"
PROFILE_FILE = DATA_ROOT / "personality" / "spark_profile.json"
BIJBEL_FILE = DATA_ROOT / "personality" / "spark_bijbel.json"
KB_FILE = DATA_ROOT / "knowledge" / "learned_knowledge" / "knowledge_base.json"


# Patterns per intent — order = priority (first match wins)
PATTERNS = [
    # Specifieke onderwerpen
    ("missie", [r"\b(jouw|je|spark.*?|sparks)\s+missie\b", r"\bmissie\s+(van\s+)?(jou|je|spark)\b", r"\bwat\s+is\s+je\s+missie\b"]),
    ("visie", [r"\b(jouw|je|spark.*?|sparks)\s+visie\b", r"\bvisie\s+(van\s+)?(jou|je|spark)\b", r"\bwat\s+is\s+je\s+visie\b"]),
    ("core", [r"\b(jouw|je|spark.*?|sparks)\s+core\b", r"\bcore\s+(van\s+)?(jou|je|spark)\b", r"\bwat\s+is\s+je\s+core\b", r"\bjouw\s+kern\b"]),
    ("doel", [r"\bjouw\s+doel\b", r"\bwat\s+is\s+je\s+doel\b", r"\bwaarvoor\s+(besta|ben)\s+(jij|je|u)\b", r"\bwaarom\s+(besta|ben)\s+(jij|je|u)\b", r"\bwaarvoor\s+dien\s+(jij|je|u)\b", r"\bbedoeling\s+(van\s+)?(jou|je|spark)\b", r"\bwat.*\bbedoeling\s+(van\s+)?spark\b"]),
    ("waarden", [r"\b(jouw|je)\s+waarden\b", r"\bwat\s+vind\s+(jij|je)\s+belangrijk\b", r"\b(jouw|je)\s+kernwaarden\b"]),
    ("maker", [r"\bwie\s+(heeft\s+(jou|je)|maakte\s+(jou|je)|maakt\s+(jou|je))\b", r"\b(jouw|je)\s+maker\b", r"\bwie\s+is\s+(jouw|je)\s+(maker|schepper|bouwer)\b"]),
    # Algemeen "wie/wat kan/anders"
    ("wat_kan", [r"\bwat\s+kan\s+(jij|je|spark)\b", r"\bwat\s+doe\s+(jij|je)\b", r"\bwaar\s+ben\s+(jij|je)\s+goed\s+in\b", r"\bvaardigheden\b"]),
    ("anders_dan", [r"\bwat\s+maakt\s+(jou|je)\s+(anders|bijzonder|uniek)\b", r"\bwat\s+is\s+er\s+anders\s+aan\s+(jou|je)\b", r"\bverschil.*andere?\s+ai\b"]),
    ("over_jezelf", [r"\bvertel\s+(eens\s+)?over\s+(jezelf|jou|spark)\b", r"\bstel\s+je\s+voor\b", r"\bintroduceer\s+je\b"]),
    ("wie_ben_je", [r"\bwie\s+(ben|bent)\s+(jij|je|u)\b", r"\bwat\s+ben\s+je\b", r"\bwat\s+ben\s+jij\b"]),
]


def _load_all():
    return {
        "identity": load_json(IDENTITY_FILE, default={}),
        "profile": (load_json(PROFILE_FILE, default={}) or {}).get("spark_profiel", {}),
        "bijbel": load_json(BIJBEL_FILE, default={}),
        "kb": load_json(KB_FILE, default={}),
    }


def _find_kb_entry(kb: dict, begrip_lower: str) -> Optional[dict]:
    """Zoek kaart met exacte begrip-match (case-insensitive)."""
    for e in kb.get("knowledge_entries", []):
        if str(e.get("begrip", "")).strip().lower() == begrip_lower:
            return e
    return None


def _laag1(entry: Optional[dict]) -> str:
    if not entry:
        return ""
    return (entry.get("lagen") or {}).get("laag1", "") or ""


def detect_intent(text: str) -> Optional[str]:
    """Retourneert intent-key of None."""
    if not text:
        return None
    t = text.lower().strip()
    for intent_key, patterns in PATTERNS:
        for pat in patterns:
            if re.search(pat, t):
                return intent_key
    return None


def build_answer(intent: str, user_naam: Optional[str] = None) -> Optional[Dict]:
    """Bouw antwoord op basis van intent. Returnt None als data ontbreekt."""
    data = _load_all()
    identity = data["identity"]
    profile = data["profile"]
    kb = data["kb"]
    bio = profile.get("biografie", {})
    name_part = f", {user_naam}" if user_naam else ""

    if intent == "wie_ben_je":
        traits = identity.get("persoonlijkheid", {}).get("traits", [])
        traits_str = ", ".join(traits[:3]).lower() if traits else "lerend en behulpzaam"
        maker = identity.get("maker", "Willem Spakman")
        doel = identity.get("doel", "")
        parts = [
            f"Hoi{name_part}! Ik ben **Spark** — een persoonlijke, lerende AI gemaakt door {maker}.",
            f"Ik ben {traits_str}.",
        ]
        if doel:
            parts.append(f"Mijn doel: {doel.lower()}.")
        parts.append("\nVraag gerust naar mijn _missie_, _visie_, _core_ of _wat ik kan_.")
        return {"message": "\n\n".join(parts), "type": "identity_intro", "intent": intent}

    if intent == "wat_kan":
        wat_kan_lijst = identity.get("basis_kennis", {}).get("wat_ik_kan", [])
        vaardig = profile.get("vaardigheden", {})
        bullets = []
        for item in wat_kan_lijst[:6]:
            bullets.append(f"• {item}")
        # Voeg een paar uit profile.vaardigheden toe indien aanwezig
        if isinstance(vaardig, dict):
            for k, v in list(vaardig.items())[:3]:
                if isinstance(v, str) and v.strip():
                    bullets.append(f"• {k.replace('_', ' ').capitalize()}: {v[:80]}")
        if not bullets:
            return None
        # v4_self_delete_001: extra hint over account delete commando in help
        return {
            "message": f"Wat ik kan{name_part}:\n\n" + "\n".join(bullets) + "\n\n_Typ **help** voor de volledige commando-lijst. Wil je je account verwijderen? Zeg het gewoon: 'verwijder mijn account'._",
            "type": "identity_what_can",
            "intent": intent,
        }

    if intent == "missie":
        # Voorkeur: profile.biografie.missie, anders kaart "Missie (visie)" of "Missie"
        missie = bio.get("missie", "").strip()
        if not missie:
            kaart = _find_kb_entry(kb, "missie") or _find_kb_entry(kb, "missie (visie)")
            missie = _laag1(kaart)
        if not missie:
            return None
        return {"message": f"**Mijn missie:**\n\n{missie}", "type": "identity_missie", "intent": intent}

    if intent == "visie":
        visie = bio.get("visie", "").strip()
        if not visie:
            kaart = _find_kb_entry(kb, "visie")
            visie = _laag1(kaart)
        if not visie:
            return None
        return {"message": f"**Mijn visie:**\n\n{visie}", "type": "identity_visie", "intent": intent}

    if intent == "core":
        # Voorkeur: profile.core_definitie of biografie.kernwaarden, anders kaart "Core"
        core_def = profile.get("core_definitie", "")
        if isinstance(core_def, dict):
            core_def = core_def.get("definitie", "") or core_def.get("kern", "")
        core_def = (core_def or "").strip()
        if not core_def:
            kaart = _find_kb_entry(kb, "core")
            core_def = _laag1(kaart)
        if not core_def:
            return None
        return {"message": f"**Mijn core:**\n\n{core_def}", "type": "identity_core", "intent": intent}

    if intent == "doel":
        waarom = bio.get("waarom_gemaakt", "").strip()
        doel = identity.get("doel", "").strip()
        if waarom:
            return {"message": f"**Waarom ik besta:**\n\n{waarom}", "type": "identity_doel", "intent": intent}
        if doel:
            return {"message": f"**Mijn doel:** {doel}", "type": "identity_doel", "intent": intent}
        return None

    if intent == "waarden":
        waarden = bio.get("kernwaarden") or bio.get("waarden") or identity.get("kernwaarden", [])
        if isinstance(waarden, str):
            return {"message": f"**Mijn waarden:**\n\n{waarden}", "type": "identity_waarden", "intent": intent}
        if isinstance(waarden, list) and waarden:
            bullets = "\n".join(f"• {w}" for w in waarden[:8])
            return {"message": f"**Mijn kernwaarden:**\n\n{bullets}", "type": "identity_waarden", "intent": intent}
        # Fallback: bijbel.kernwaarden
        bijbel_kw = data["bijbel"].get("kernwaarden") or []
        if isinstance(bijbel_kw, list) and bijbel_kw:
            bullets = "\n".join(f"• {w}" for w in bijbel_kw[:8])
            return {"message": f"**Mijn kernwaarden:**\n\n{bullets}", "type": "identity_waarden", "intent": intent}
        return None

    if intent == "maker":
        maker = identity.get("maker", "Willem Spakman")
        gesch = bio.get("geschiedenis", "")
        msg = f"Ik ben gemaakt door **{maker}**."
        if gesch:
            msg += f"\n\n{gesch[:280]}"
        return {"message": msg, "type": "identity_maker", "intent": intent}

    if intent == "anders_dan":
        waarom = bio.get("waarom_gemaakt", "").strip()
        if waarom:
            # Pak de "kern"-zin
            return {
                "message": f"**Wat me anders maakt:**\n\n{waarom}",
                "type": "identity_uniek",
                "intent": intent,
            }
        return None

    if intent == "over_jezelf":
        # Combineer: korte intro + missie kort + wat kan ik
        intro_res = build_answer("wie_ben_je", user_naam)
        intro = intro_res["message"] if intro_res else ""
        missie = bio.get("missie", "").strip()
        bullets = identity.get("basis_kennis", {}).get("wat_ik_kan", [])[:4]
        parts = [intro]
        if missie:
            parts.append(f"\n**Missie:** {missie[:200]}")
        if bullets:
            parts.append("\n**Ik kan onder andere:**\n" + "\n".join(f"• {b}" for b in bullets))
        return {"message": "\n".join(parts), "type": "identity_intro_full", "intent": intent}

    return None


def try_answer(text: str, user_naam: Optional[str] = None) -> Optional[Dict]:
    """Hoofdingang: detecteer + bouw antwoord. None = geen identity-intent."""
    intent = detect_intent(text)
    if not intent:
        return None
    return build_answer(intent, user_naam=user_naam)
