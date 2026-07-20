"""
Self-Profile Intent (v9_self_profile_001)
==========================================
Detecteert wanneer de user vraagt naar zijn EIGEN gegevens (waar woon ik,
wat is mijn adres/email/telefoon, mijn profiel, etc.) en antwoordt DIRECT uit
`data/users/{user_id}/profile.json`.

Fixes:
- User: "waar woon ik" → Spark vroeg om verificatie, terwijl user gewoon
  toegang heeft tot eigen data.
- Auth-model: als user ingelogd is (user_id != None) is dat de verificatie.
  Verificatie-drempel geldt voor VREEMDE user's data, niet eigen.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any

from modules.core.storage import load_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"


# Vraagpatronen — direct-verwijzend naar EIGEN gegevens
_SELF_PROFILE_PATTERNS = [
    r"\bwaar\s+woon\s+ik\b",
    r"\bwat\s+is\s+(m'?n?|mijn)\s+(adres|straat|postcode|plaats|woonplaats|stad|email|telefoon|iban)\b",
    r"\b(m'?n?|mijn)\s+(adres|straat|postcode|plaats|woonplaats|stad|email|telefoon|iban)\b",
    r"\b(wat|welke)\s+(zijn?)\s+(m'?n?|mijn)\s+(gegevens|profielgegevens|contactgegevens|persoonlijke\s+gegevens)\b",
    r"\btoon\s+(m'?n?|mijn)\s+(profiel|gegevens|adres)\b",
    r"\bkijk\s+in\s+(m'?n?|mijn)\s+(profiel|gegevens)\b",
    r"\blees\s+(m'?n?|mijn)\s+profiel\b",
]

# Specifiek per veld — voor gerichte antwoorden
_FIELD_PATTERNS = {
    "adres":       [r"waar\s+woon\s+ik", r"m'?n?\s*adres", r"mijn\s+adres", r"m'?n?\s*straat", r"mijn\s+straat", r"woonplaats"],
    "postcode":    [r"m'?n?\s*postcode", r"mijn\s+postcode"],
    "plaats":      [r"welke\s+plaats", r"welke\s+stad", r"m'?n?\s*plaats", r"mijn\s+plaats", r"m'?n?\s*stad", r"mijn\s+stad"],
    "email":       [r"m'?n?\s*email", r"mijn\s+email", r"e-?mail"],
    "telefoon":    [r"m'?n?\s*telefoon", r"mijn\s+telefoon", r"m'?n?\s*telefoonnummer", r"mijn\s+telefoonnummer"],
    "iban":        [r"m'?n?\s*iban", r"mijn\s+iban", r"bankrekening", r"rekeningnummer"],
    "geboortedatum": [r"m'?n?\s*(geboortedatum|verjaardag)", r"mijn\s+(geboortedatum|verjaardag)", r"wanneer\s+ben\s+ik\s+geboren"],
    "profiel":     [r"profielgegevens", r"contactgegevens", r"toon\s+(m'?n?|mijn)\s+profiel", r"lees\s+(m'?n?|mijn)\s+profiel"],
}


def _detect_field(text: str) -> Optional[str]:
    """Return specifiek profiel-veld dat gevraagd wordt (of 'profiel' voor volledig)."""
    t = text.lower()
    for field, patterns in _FIELD_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, t):
                return field
    return None


def _load_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Lees profile.json voor deze user."""
    p = DATA_ROOT / "users" / user_id / "profile.json"
    if not p.exists():
        return None
    return load_json(p, default=None)


def _format_field(profile: Dict[str, Any], field: str, user_naam: str) -> str:
    """Format een specifiek antwoord met bronvermelding."""
    prefix = f"**{user_naam}**, volgens jouw profiel:"
    src = "\n\n📁 _Bron: `data/users/user-001/profile.json`_"
    if field == "adres":
        straat = profile.get("straat", "")
        postcode = profile.get("postcode", "")
        plaats = profile.get("plaats", "")
        land = profile.get("land", "")
        line = f"{straat}, {postcode} {plaats}, {land}".strip(", ")
        return f"{prefix}\n\n🏠 Je woont op **{line}**{src}"
    if field == "postcode":
        return f"{prefix}\n\n📮 Je postcode is **{profile.get('postcode', 'onbekend')}**{src}"
    if field == "plaats":
        return f"{prefix}\n\n🏙️ Je woont in **{profile.get('plaats', 'onbekend')}**{src}"
    if field == "email":
        return f"{prefix}\n\n📧 Je e-mailadres is **{profile.get('email', 'onbekend')}**{src}"
    if field == "telefoon":
        return f"{prefix}\n\n📞 Je telefoonnummer is **{profile.get('telefoon', 'onbekend')}**{src}"
    if field == "iban":
        iban = profile.get("iban", "onbekend")
        bank = profile.get("bank_provider", "")
        return f"{prefix}\n\n🏦 Je IBAN is **{iban}**" + (f" ({bank})" if bank else "") + src
    if field == "geboortedatum":
        return f"{prefix}\n\n🎂 Je bent geboren op **{profile.get('geboortedatum', 'onbekend')}**{src}"
    if field == "profiel":
        lines = [prefix, ""]
        pairs = [
            ("Volledige naam", profile.get("volledige_naam")),
            ("E-mail", profile.get("email")),
            ("Telefoon", profile.get("telefoon")),
            ("Adres", f"{profile.get('straat', '')}, {profile.get('postcode', '')} {profile.get('plaats', '')}".strip(", ")),
            ("Land", profile.get("land")),
            ("Geboortedatum", profile.get("geboortedatum")),
            ("Nationaliteit", profile.get("nationaliteit")),
            ("Bank/IBAN", f"{profile.get('bank_provider', '')} — {profile.get('iban', '')}".strip(" —")),
        ]
        for k, v in pairs:
            if v:
                lines.append(f"• **{k}**: {v}")
        return "\n".join(lines) + src
    return f"{prefix}\n\n_(veld '{field}' niet in profiel gevonden)_"


def try_detect(text: str, user_id: str = "user-001") -> Optional[Dict[str, Any]]:
    """Return {intent, message, action, data, fast_path} of None."""
    if not text or not isinstance(text, str):
        return None
    t = text.strip().lower()

    # Match algemeen intent-patroon
    if not any(re.search(p, t) for p in _SELF_PROFILE_PATTERNS):
        return None

    # Detecteer specifiek veld
    field = _detect_field(text) or "profiel"

    # Lees profiel
    profile = _load_profile(user_id)
    if not profile:
        return {
            "intent": "self_profile",
            "message": f"Ik kan je profiel-bestand `data/users/{user_id}/profile.json` niet lezen. Bestaat het al?",
            "action": "self_profile_missing",
            "fast_path": True,
        }

    user_naam = profile.get("volledige_naam") or "onbekend"
    return {
        "intent": "self_profile",
        "message": _format_field(profile, field, user_naam.split()[0] if user_naam else "user"),
        "action": "self_profile_read",
        "data": {"field": field, "source": f"data/users/{user_id}/profile.json"},
        "fast_path": True,
    }
