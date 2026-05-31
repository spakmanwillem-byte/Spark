"""
v6_warmth_layer_001 — Norm/waarden/bijbel komen tot de spraak.

Doel: het bijbel-systeem (kernwaarden + normen) niet langer alleen detecteren in
shadow, maar **echt** in de chat-response weven — voorzichtig, alleen waar nodig.

Wanneer activeert deze laag?
  • Pipeline detecteert sterke of escalerende emotie (L2 weging)
  • Pipeline adviseert een ACTIEVE behavior_class:
      - begrenzen-structureren  (boos)
      - vertragen-ondersteunen (bedroefd)
      - kalmeren-opties        (bang)
  • Huidige route is INFORMATIEF (snap/knowledge/fallback/unknown)
      → exact het gat dat de A/B diff aanwijst (sessie 12: "60% match, vaak knowledge ipv
        emotie-route bij negatieve input")

Wat doet het?
  • Prepend één korte erkenningszin (uit kernwaarde-laag1) vóór de info-response.
  • Niet vervangen — Spark geeft nog steeds de kennis. Hij ZIET de mens eerst.

Wat doet het NIET?
  • Niet activeren bij greeting/goodbye/agenda/identity/help/time/capability — die
    hebben hun eigen passende toon al.
  • Niet hardcoden: gebruikt de laag1-tekst uit spark_bijbel.json zodat De Willem
    de toon kan tunen zonder code te wijzigen.
  • Niet stapelen: max 1 warmte-prefix per response.
"""
from pathlib import Path
from typing import Optional, Dict
import random

from ..core.storage import load_json

BIJBEL_FILE = Path(__file__).parent.parent.parent / "data" / "personality" / "spark_bijbel.json"

# Routes waarbij we WEL warmte prepen (info-routes die de emotie miskennen)
INFO_ROUTES = {
    "knowledge", "snap", "snap_response", "fallback",
    "unknown", "kbv2_tell_layer", "kbv2_tell_kort", "kbv2_tell_meer",
    "compositional", "auto_snap",
}

# Routes die we NOOIT met warmte mogen vervuilen (hebben eigen toon)
SKIP_ROUTES = {
    "greeting", "goodbye", "thanks", "help", "agenda_proposal",
    "agenda_add", "identity", "time_now", "capability", "kasboek_overzicht",
    "wedervraag", "safeword", "dnd_help", "trade_help",
    "bots_status", "audit_health",
}

# Welke behavior_class → welke korte erkenningszinnen (fallback als bijbel laag1 ontbreekt)
BEHAVIOR_FALLBACKS = {
    "begrenzen-structureren": [
        "Ik hoor dat het schuurt.",
        "Snap dat dit niet lekker zit.",
        "Begrijpelijk dat dit knelt.",
    ],
    "vertragen-ondersteunen": [
        "Even rust nemen mag.",
        "Snap dat het zwaar voelt.",
        "Geen haast, ik blijf bij je.",
    ],
    "kalmeren-opties": [
        "We doen het stap voor stap.",
        "Geen zorgen, we kijken samen.",
        "Even rustig, één ding tegelijk.",
    ],
}


def _load_bijbel() -> Dict:
    return load_json(BIJBEL_FILE, default={"kernwaarden": [], "normen": []})


def _pick_warmth_line(kernwaarde_naam: Optional[str], behavior: str) -> Optional[str]:
    """Pak een korte zin uit de kernwaarde laag1, met fallback."""
    if kernwaarde_naam:
        bijbel = _load_bijbel()
        for w in bijbel.get("kernwaarden", []):
            if w.get("waarde", "").lower() == kernwaarde_naam.lower():
                laag1 = (w.get("lagen", {}) or {}).get("laag1", "").strip()
                if laag1 and len(laag1) < 80:
                    return laag1
                # Als laag1 te lang of leeg: pak eerste zin van beschrijving
                desc = (w.get("beschrijving", "") or "").strip()
                if desc:
                    first_sentence = desc.split(". ")[0].strip()
                    if first_sentence and len(first_sentence) < 80:
                        return first_sentence + "."
                break
    # Fallback: behavior-class gebaseerd
    pool = BEHAVIOR_FALLBACKS.get(behavior, [])
    return random.choice(pool) if pool else None


def should_apply_warmth(
    pipeline_summary: Optional[Dict],
    current_route: Optional[str],
) -> bool:
    """Beslis of warmte-laag mag aanvullen op deze response."""
    if not pipeline_summary:
        return False
    behavior = pipeline_summary.get("behavior")
    weging = pipeline_summary.get("weging")
    if behavior not in BEHAVIOR_FALLBACKS:
        return False
    # Alleen bij sterke/escalerende emotie — niet bij licht
    if weging not in ("sterk", "escalerend"):
        return False
    route = (current_route or "").lower()
    if route in SKIP_ROUTES:
        return False
    if route in INFO_ROUTES:
        return True
    # Onbekende route: standaard niet warmen (veilig)
    return False


def maybe_apply_warmth(
    response: Dict,
    pipeline_summary: Optional[Dict],
    current_route: Optional[str],
) -> Dict:
    """
    Muteer response['message'] in-place met een erkenningszin als alle voorwaarden
    voldoen. Markeer `warmth_applied=True` voor traceability.

    Returnt response (zelfde object).
    """
    if not should_apply_warmth(pipeline_summary, current_route):
        return response
    msg = response.get("message")
    if not msg or not isinstance(msg, str):
        return response
    # Anti-stapel: niet 2× prefixen in dezelfde session-flow
    if response.get("warmth_applied"):
        return response

    behavior = pipeline_summary.get("behavior")
    kernwaarde = pipeline_summary.get("kernwaarde")
    line = _pick_warmth_line(kernwaarde, behavior)
    if not line:
        return response

    # Voorkom dubbele punctuatie + behoud emoji/format
    sep = " " if not msg.startswith(("\n", "•", "-")) else "\n\n"
    response["message"] = f"{line}{sep}{msg}"
    response["warmth_applied"] = True
    response["warmth_meta"] = {
        "kernwaarde": kernwaarde,
        "behavior": behavior,
        "line": line,
        "from_route": current_route,
    }
    return response
