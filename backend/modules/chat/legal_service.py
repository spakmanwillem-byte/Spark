"""
Legal Intent Service — privacy / cookies / voorwaarden
Detect vragen en formatteer secties uit JSON.
Storage:
  /data/system/legal_privacy.json
  /data/system/legal_cookies.json
  /data/system/legal_voorwaarden.json
"""
import re
from pathlib import Path
from typing import Dict, Optional

from modules.core.storage import load_json

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "system"


_PRIVACY_PATTERNS = [
    r"\bprivacy\b",
    r"\bwat (is|zijn) (de )?privacy\s*(beschrijving|voorwaarden|policy|verklaring)?\b",
    r"\bhoe (ga|gaat) (je|spark) (om|met) mijn data\b",
    r"\bwat (doe|doet) (je|spark) (met )?(mijn )?gegevens\b",
]
_COOKIES_PATTERNS = [
    r"\bcookies?\b",
    r"\bwat (is|zijn) (de )?cookie[s]?\s*(verklaring|beschrijving|policy)?\b",
    r"\blocalstorage\b",
    r"\bsessionstorage\b",
]
_TERMS_PATTERNS = [
    r"\bvoorwaarden\b",
    r"\bgebruiksvoorwaarden\b",
    r"\bwat (zijn|is) de (voorwaarden|terms|regels)\b",
    r"\bterms (of|and) (service|use|conditions)\b",
]


def detect_legal_intent(text: str) -> Optional[str]:
    """Geeft 'privacy' | 'cookies' | 'voorwaarden' | None terug."""
    if not text:
        return None
    t = text.lower().strip()
    if any(re.search(p, t) for p in _PRIVACY_PATTERNS):
        return "privacy"
    if any(re.search(p, t) for p in _COOKIES_PATTERNS):
        return "cookies"
    if any(re.search(p, t) for p in _TERMS_PATTERNS):
        return "voorwaarden"
    return None


_LABELS = {
    "privacy":      ("Privacy Beschrijving", "🔒", "legal_privacy.json"),
    "cookies":      ("Cookies & Opslag", "🍪", "legal_cookies.json"),
    "voorwaarden":  ("Gebruiksvoorwaarden", "📜", "legal_voorwaarden.json"),
}


def handle_legal(kind: str) -> Dict:
    """Format de JSON-content als chat-bericht."""
    label, emoji, fname = _LABELS.get(kind, ("?", "📄", ""))
    data = load_json(DATA_DIR / fname, default={})
    if not data:
        return {
            "type": f"legal_{kind}",
            "message": f"{emoji} **{label}** — nog niet ingevuld. Vraag de admin om dit op te stellen.",
            "response_type": "legal",
        }

    lines = [f"{emoji} **{label}** _(versie {data.get('version', '—')})_", ""]
    if data.get("intro"):
        lines.append(data["intro"])
        lines.append("")

    for sectie in data.get("secties", []):
        lines.append(f"**{sectie.get('titel', '—')}**")
        if sectie.get("tekst"):
            lines.append(sectie["tekst"])
        for item in sectie.get("items", []):
            lines.append(f"  • {item}")
        # cookies-stijl: doel/duur/delen rows
        for k in ("doel", "duur", "delen"):
            if sectie.get(k):
                lines.append(f"  · _{k.capitalize()}_: {sectie[k]}")
        lines.append("")

    if data.get("third_party"):
        lines.append(f"_Third-party_: {data['third_party']}")
        lines.append("")
    if data.get("contact"):
        lines.append(f"_{data['contact']}_")

    return {"type": f"legal_{kind}", "message": "\n".join(lines), "response_type": "legal"}
