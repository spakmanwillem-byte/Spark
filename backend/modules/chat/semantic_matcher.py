"""v6_semantic_intent_matcher_001 — Spark legt zelf verbanden tussen synoniemen.

Werkt na de exact-match fast-path en VÓÓR de LLM-call. Gebruikt rapidfuzz's
token-set ratio voor robuuste fuzzy matching (orde-onafhankelijk, herkent ook
hertaalde of geparafraseerde commands).

Doel: voorkomen dat ik bij elke nieuwe trigger ('open spel sps' / 'doe rps' /
'kunnen we sps') de lijst handmatig moet uitbreiden. Spark zelf snapt het.

Catalog: per action een set van canonical-zinnen + drempel. Bij user-text die
boven drempel scoort op een van de canonical-zinnen → return die action.

Lokaal, snel (~5ms), geen LLM-call, deterministisch.
"""
from typing import Dict, List, Optional, Any, Tuple

try:
    from rapidfuzz import fuzz
    _RF_OK = True
except Exception:
    _RF_OK = False


# Catalog: action_id → {canonical: list[str], min_score: int, response: dict}
# Score 0-100 (rapidfuzz token_set_ratio). Min 75 = duidelijke match.
_CATALOG: List[Dict[str, Any]] = [
    {
        "action": "open_game_rps",
        "canonical": [
            "speel steen papier schaar",
            "speel sps",
            "open sps",
            "begin sps",
            "start sps",
            "doe een potje sps",
            "kunnen we sps spelen",
            "ik wil sps doen",
            "laten we een spelletje doen",
            "spelletje spelen",
        ],
        "min_score": 78,
        "response": {
            "type": "open_game",
            "action": "open_game_rps",
            "rps_opponent": "spark",
            "message": "🎮 Steen — Papier — Schaar! Kies je zet.",
            "used_model": "semantic_matcher",
            "log_channel": "spark-deep-rps-sem",
        },
    },
    {
        "action": "enable_tts",
        "canonical": [
            "tts aan",
            "zet text to speech aan",
            "spreek je antwoorden uit",
            "ik wil je horen praten",
            "zet je stem aan",
        ],
        "min_score": 80,
        "response": {
            "type": "action_tts_on",
            "action": "enable_tts",
            "message": "Text-to-Speech aan. Vanaf nu spreek ik mijn antwoord uit.",
            "used_model": "semantic_matcher",
            "log_channel": "spark-deep-action-sem",
        },
    },
    {
        "action": "disable_tts",
        "canonical": [
            "tts uit",
            "zet text to speech uit",
            "stop met praten",
            "wees stil",
            "geen stem meer",
        ],
        "min_score": 80,
        "response": {
            "type": "action_tts_off",
            "action": "disable_tts",
            "message": "Text-to-Speech uit. Ik ben weer stil.",
            "used_model": "semantic_matcher",
            "log_channel": "spark-deep-action-sem",
        },
    },
    {
        "action": "open_help_bark",
        "canonical": [
            "geef me een overzicht van commando's",
            "ik wil een commando-lijst",
            "welke mogelijkheden zijn er",
            "toon help kader",
            "open help paneel",
        ],
        "min_score": 85,
        "response": {
            "type": "open_help_bark",
            "action": "open_help_bark",
            "message": "🔮 Help-overzicht geopend.",
            "used_model": "semantic_matcher",
            "log_channel": "spark-deep-help-sem",
        },
    },
]


def semantic_match(user_text: str, debug: bool = False) -> Optional[Dict[str, Any]]:
    """Zoek de best-passende action voor de user-text via fuzzy similarity.

    Returns: dict met action/url/message/etc. of None als geen match boven drempel.
    """
    if not _RF_OK:
        return None
    if not user_text or not isinstance(user_text, str):
        return None
    t = user_text.lower().strip()
    if not t or len(t) > 200:  # te lange tekst = waarschijnlijk geen command
        return None

    best: Optional[Tuple[int, Dict[str, Any], str]] = None
    for entry in _CATALOG:
        for canon in entry["canonical"]:
            score = fuzz.token_set_ratio(t, canon.lower())
            if score >= entry["min_score"]:
                if best is None or score > best[0]:
                    best = (score, entry, canon)

    if not best:
        return None

    score, entry, canon = best
    resp = dict(entry["response"])  # shallow copy
    resp["semantic_score"] = score
    resp["semantic_matched_canonical"] = canon
    resp["used_cards"] = []
    resp["blueprint_version"] = "1.0"
    resp["fast_path"] = True
    resp["success"] = True
    if debug:
        print(f"[semantic_match] '{t}' → action={entry['action']} score={score} via '{canon}'")
    return resp
