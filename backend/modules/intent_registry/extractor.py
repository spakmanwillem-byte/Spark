"""
Intent Extractor v1 — keyword + emotie-lens → tag_vector
================================================================================
v6_command_registry_001 — Fundering voor donderdag's bidirectionele matcher.

Doel: zet user-text om in tag_vector zodat capability-matcher tag-overlap kan
scoren tegen command_registry.json.

v1 is keyword-based (geen LLM). Donderdag mogelijk upgraden naar LLM via
emergentintegrations als matching te zwak blijkt.

Voorbeeld:
  "Wat staat morgen op mijn agenda?"
   → ["tijd", "morgen", "agenda", "planning", "bekijken"]
"""
from typing import List, Optional, Dict
import re

# Basis-tag woordenboek: synoniem → canonical tag
_KEYWORD_MAP = {
    # tijd
    "vandaag": "tijd", "morgen": "morgen", "gisteren": "gisteren",
    "nu": "tijd", "tijd": "tijd", "wanneer": "tijd", "datum": "tijd",
    # planning / agenda
    "agenda": "agenda", "afspraak": "agenda", "planning": "planning",
    "plannen": "planning", "plan": "planning",
    # bekijken / lijst
    "zie": "bekijken", "bekijk": "bekijken", "toon": "bekijken", "laat zien": "bekijken",
    "lijst": "lijst", "overzicht": "overzicht", "lijstje": "lijst",
    # tellen
    "hoeveel": "tellen", "aantal": "tellen", "tel": "tellen", "tellen": "tellen",
    # gebruikers
    "gebruikers": "gebruikers", "leden": "gebruikers", "users": "gebruikers",
    # taken
    "taak": "taken", "taken": "taken", "todo": "taken", "to-do": "taken",
    "openstaand": "openstaand", "open": "openstaand",
    # notities
    "notitie": "notitie", "noteer": "notitie", "memo": "notitie",
    "onthoud": "onthouden", "onthouden": "onthouden",
    # wallet / geld
    "geld": "geld", "saldo": "saldo", "balance": "saldo", "wallet": "wallet",
    "tikkie": "tikkie", "opwaardeer": "topup", "topup": "topup",
    "kasboek": "kasboek", "boekhouding": "kasboek",
    "transactie": "transacties", "transacties": "transacties", "uitgave": "uitgaven",
    # trade / crypto
    "trade": "trade", "trader": "trade", "trading": "trade",
    "koop": "kopen", "kopen": "kopen", "buy": "kopen",
    "verkoop": "verkopen", "verkopen": "verkopen", "sell": "verkopen",
    "winst": "winst", "verlies": "verlies", "pnl": "winst",
    "coin": "crypto", "coins": "crypto", "crypto": "crypto", "bitcoin": "crypto", "btc": "crypto",
    "ethereum": "crypto", "eth": "crypto", "sol": "crypto", "ada": "crypto",
    "watchlist": "watchlist", "monitor": "monitor",
    # kennis
    "weet": "weten", "weten": "weten", "ken": "weten", "kennis": "kennis",
    "wat is": "uitleg", "leg uit": "uitleg", "vertel": "uitleg",
    "uitleg": "uitleg", "begrip": "begrip", "betekenis": "uitleg",
    # audit
    "audit": "audit", "scan": "scan", "missing": "missend", "gaten": "missend",
    # bijbel / ethiek
    "bijbel": "bijbel", "norm": "normen", "normen": "normen",
    "waarde": "waarden", "waarden": "waarden", "kernwaarde": "kernwaarde",
    "ethiek": "ethiek", "moraal": "moraal", "principe": "moraal",
    # spark identity
    "wie ben jij": "identiteit", "wie ben je": "identiteit",
    "spark": "spark", "identiteit": "identiteit",
    # community
    "groep": "community", "community": "community", "iedereen": "community",
    # archief / media
    "foto": "afbeelding", "afbeelding": "afbeelding", "plaatje": "afbeelding",
    "geluid": "geluid", "audio": "geluid", "muziek": "geluid", "stem": "geluid",
    "bestand": "bestanden", "bestanden": "bestanden", "archief": "archief",
    # gesprek / chat
    "gesprek": "gesprek", "chat": "chat", "bericht": "bericht",
    "terug": "terugkijken", "terugkijken": "terugkijken",
    "geschiedenis": "geschiedenis", "log": "log",
    # dagboek
    "dagboek": "dagboek", "diary": "dagboek", "reflectie": "reflectie",
    "mood": "mood", "stemming": "mood",
    # achievements
    "achievement": "achievement", "milestone": "achievement",
    "xp": "xp", "punt": "xp", "punten": "xp",
    "behaald": "achievement",
    # leaderboard
    "leaderboard": "leaderboard", "ranglijst": "leaderboard", "podium": "leaderboard",
    "top": "top", "score": "score",
    # emoties → pipeline-tags meelopen
    "voel": "voelen", "voelen": "voelen", "emotie": "emotie",
    # disclaimer
    "disclaimer": "disclaimer", "grenzen": "grenzen", "kader": "kaders",
    "doe je niet": "grenzen",
    # v6_winkelstraat_001 — shop intents
    "winkel": "winkel", "shop": "winkel", "winkeltje": "winkel",
    "winkelstraat": "winkelstraat", "merch": "merch", "digitaal": "digitaal",
    "product": "product", "producten": "product",
    # v6_glow_nav_001 — navigation intents
    "waar is": "navigate", "ga naar": "navigate", "open": "navigate_open",
    "tab": "tab", "pagina": "pagina", "scherm": "pagina",
    # help
    "help": "help", "wat kan jij": "help", "hulp": "help", "commando": "commands",
}

# Multi-word fragments (worden vóór tokenisatie gematcht zodat "wat is" → "uitleg")
_MULTIWORD = [
    "wie ben jij", "wie ben je",
    "wat is", "leg uit",
    "doe je niet", "laat zien",
    "to-do",
    "waar is", "ga naar", "wat kan jij",
]


def extract_tags(text: str, emotion_pipeline_summary: Optional[Dict] = None) -> List[str]:
    """User-text → tag_vector via keyword-map + multi-word + emotie-lens.

    Args:
      text: ruwe user input
      emotion_pipeline_summary: optionele output van emotion_pipeline.run_pipeline
        — als aanwezig, worden behavior_class + kernwaarde als tags meegenomen.

    Returns:
      Geordende lijst unieke tags (eerst keyword-matches, dan emotion-lens).
    """
    if not text:
        return []
    t = text.lower().strip()

    tags: List[str] = []
    seen = set()

    def _add(tag: str):
        if tag and tag not in seen:
            tags.append(tag)
            seen.add(tag)

    # 1) Multi-word matches eerst (anders worden ze losgeknipt)
    for phrase in _MULTIWORD:
        if phrase in t:
            canon = _KEYWORD_MAP.get(phrase)
            if canon:
                _add(canon)
            # Vervang voor tokenisatie zodat losse woorden niet dubbel matchen
            t = t.replace(phrase, " ")

    # 2) Single-word matches
    words = re.findall(r"[\wàáèéëïóöü-]+", t, flags=re.UNICODE)
    for w in words:
        canon = _KEYWORD_MAP.get(w)
        if canon:
            _add(canon)

    # 3) Emotie-pipeline lens-tags toevoegen
    if emotion_pipeline_summary and isinstance(emotion_pipeline_summary, dict):
        if emotion_pipeline_summary.get("emotie"):
            _add(f"emo:{emotion_pipeline_summary['emotie']}")
        if emotion_pipeline_summary.get("behavior"):
            _add(f"behavior:{emotion_pipeline_summary['behavior']}")
        if emotion_pipeline_summary.get("kernwaarde"):
            _add(f"waarde:{emotion_pipeline_summary['kernwaarde'].lower()}")

    return tags
