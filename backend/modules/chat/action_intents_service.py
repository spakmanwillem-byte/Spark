"""
Action Intents Service (v4_actions_001) — Spark herkent chat-commando's voor app-acties.

Twee groepen:
  1) Speech-to-Text aan/uit (STT)
  2) Ambient achtergrondgeluid aan/uit (vogels-loop e.d.)

Response bevat een 'action' veld dat frontend interpreteert:
  - { action: "enable_stt" }
  - { action: "disable_stt" }
  - { action: "play_ambient", loop_id: "birds_loop_01", url: "/api/system/ambient/birds_loop_01.wav" }
  - { action: "stop_ambient" }
"""
import re
import json
from pathlib import Path
from typing import Optional, Dict

from modules.chat import intent_pattern_store as _patterns  # v13d_intent_patterns_json_001

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
AMBIENT_DIR = DATA_ROOT / "system" / "ambient"
AMBIENT_REGISTRY = AMBIENT_DIR / "registry.json"


# v13d_intent_patterns_json_001 — regex-patronen leven nu in
# `intent_pattern_store` (BASELINE + JSON). Handmatig toevoegen via
# /api/triggers/edit/intent/{stt_on|stt_off|tts_on|tts_off|ambient_off}/add.


_RX_TTSS = re.compile(r"^\s*\(?\s*(ttss|gtss)\s*(aan|uit|on|off)\s*\)?\s*$", re.IGNORECASE)


def _match_any(text: str, intent_key: str) -> bool:
    return _patterns.match_any(intent_key, text or "")


def _load_loops():
    if not AMBIENT_REGISTRY.exists():
        return []
    try:
        return (json.loads(AMBIENT_REGISTRY.read_text()) or {}).get("loops", [])
    except Exception:
        return []


def _detect_ambient_on(text: str) -> Optional[dict]:
    """Vind een loop op basis van genummerde trigger ('ambient1', 'ambient 2') of expliciet woord.
    Voorbeelden: 'ambient 1 aan', 'ambient2 aan', 'speel ambient 1', 'vogels aan'."""
    t = text.lower()
    # 1) Genummerde lookup: 'ambient 1' / 'ambient1' / 'ambient nr 1'
    m = re.search(r"\bambient\s*(?:nr\.?\s*)?(\d+)\b", t)
    if m:
        nr = int(m.group(1))
        for loop in _load_loops():
            if loop.get("ambient_nr") == nr:
                # action-woord nodig om play te triggeren (anders zou 'ambient 1 uit' ook fire)
                if re.search(r"\b(aan|speel|start|begin|afspelen|wil|doe|zet)\b", t):
                    return loop
        return None
    # 2) Trigger-woord match
    action_words = [r"\baan\b", r"\bspeel\b", r"\bafspelen\b", r"\bdoe\b", r"\bzet\b", r"\bstart\b", r"\bbegin\b"]
    has_action = any(re.search(p, t) for p in action_words)
    for loop in _load_loops():
        for trig in loop.get("triggers", []):
            tt = trig.lower()
            if re.search(rf"\b{re.escape(tt)}\b", t):
                if has_action or "aan" in tt:  # trigger zelf bevat 'aan' bv 'ambient 1'
                    return loop
    return None


# ============== HOOFD-INGANG ==============
def try_detect(text: str) -> Optional[Dict]:
    """Detecteer een action-intent. Returnt None als geen match."""
    if not text:
        return None

    # 0. v14_ttss_001 — ttss (Willems eigen stem) / gtss (kaart-geluiden) aan/uit
    m = _RX_TTSS.match(text or "")
    if m:
        kind, state = m.group(1).lower(), m.group(2).lower()
        on = state in ("aan", "on")
        if kind == "ttss":
            return {"action": "enable_ttss" if on else "disable_ttss", "type": f"action_ttss_{'on' if on else 'off'}",
                    "message": ("TTSS aan — ik spreek nu met jóuw ingesproken kaarten. Woorden zonder opname sla ik over tot je ze inspreekt."
                                if on else "TTSS uit — terug naar de gewone stem (als TTS aan staat).")}
        return {"action": "enable_gtss" if on else "disable_gtss", "type": f"action_gtss_{'on' if on else 'off'}",
                "message": ("GTSS aan — bij woorden met een kaart-geluid speel ik dat geluid af. (Placeholder: nog weinig geluiden.)"
                            if on else "GTSS uit.")}

    # 1. STT off (eerst, want "stt uit" mag niet als "stt aan" matchen)
    if _match_any(text, "stt_off"):
        return {
            "action": "disable_stt",
            "message": "Speech-to-Text uitgezet. Je kunt weer typen 🌝",
            "type": "action_stt_off",
        }

    # 2. STT on
    if _match_any(text, "stt_on"):
        return {
            "action": "enable_stt",
            "message": "Speech-to-Text aangezet — ik luister, druk de mic-knop om in te spreken. Zeg of typ 'stt uit' om te stoppen.",
            "type": "action_stt_on",
        }

    # 2b. TTS off (vóór on)
    if _match_any(text, "tts_off"):
        return {
            "action": "disable_tts",
            "message": "Text-to-Speech uit. Ik schrijf, maar zwijg verder 🤐",
            "type": "action_tts_off",
        }

    # 2c. TTS on
    if _match_any(text, "tts_on"):
        return {
            "action": "enable_tts",
            "message": "Text-to-Speech aan. Vanaf nu spreek ik mijn antwoord uit. Zeg of typ 'tts uit' om te stoppen.",
            "type": "action_tts_on",
        }

    # 3. Ambient off
    if _match_any(text, "ambient_off"):
        return {
            "action": "stop_ambient",
            "message": "Achtergrondgeluid uitgezet.",
            "type": "action_ambient_off",
        }

    # 4. Ambient on (zoek loop in registry)
    loop = _detect_ambient_on(text)
    if loop:
        return {
            "action": "play_ambient",
            "loop_id": loop["id"],
            "url": f"/api/system/ambient/{loop['filename']}",
            "label": loop.get("label", loop["id"]),
            "message": f"🎵 Speel **{loop.get('label', loop['id'])}** af op de achtergrond. Zeg 'stilte' om te stoppen.",
            "type": "action_ambient_on",
        }

    return None
