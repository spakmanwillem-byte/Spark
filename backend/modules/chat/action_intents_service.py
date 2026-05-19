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

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
AMBIENT_DIR = DATA_ROOT / "system" / "ambient"
AMBIENT_REGISTRY = AMBIENT_DIR / "registry.json"


# ============== STT ==============
STT_ON_PATTERNS = [
    r"\bspeech[-\s]?to[-\s]?text\s+(aan|aanzetten|activeren|start|aan zetten|aanzettten)\b",
    r"\bstt\s+(aan|aanzetten|activeren|start)\b",
    r"\b(zet|doe)\s+(de\s+)?(speech[-\s]?to[-\s]?text|stt|microfoon|micro|mic)\s+aan\b",
    r"\b(start|activeer)\s+(de\s+)?(speech[-\s]?to[-\s]?text|stt|microfoon|micro|mic|spraak|spraakherkenning)\b",
    r"\bik\s+wil\s+(praten|spreken|inspreken)\b",
    r"\bmicrofoon\s+aan\b",
    r"\b(luister|hoor)\s+(naar\s+)?(me|mij)\b",
]

STT_OFF_PATTERNS = [
    r"\bspeech[-\s]?to[-\s]?text\s+(uit|uitzetten|stoppen|stop|deactiveren|uit zetten)\b",
    r"\bstt\s+(uit|uitzetten|stoppen|stop|deactiveren)\b",
    r"\b(zet|doe)\s+(de\s+)?(speech[-\s]?to[-\s]?text|stt|microfoon|micro|mic)\s+uit\b",
    r"\b(stop|deactiveer)\s+(de\s+)?(speech[-\s]?to[-\s]?text|stt|microfoon|micro|mic|spraak|spraakherkenning)\b",
    r"\b(ik\s+wil\s+)?(weer\s+)?typen\b",
    r"\bmicrofoon\s+uit\b",
]


def _match_any(text: str, patterns) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


# ============== AMBIENT ==============
AMBIENT_OFF_PATTERNS = [
    r"\b(stilte|stil)\b",
    r"\bambient\s*\d*\s*(uit|stop|af|weg)\b",
    r"\b(stop|zet)\s+(de\s+)?(muziek|geluid|loop|ambient|achtergrondgeluid|natuur|vogels|vogeltjes)\s*(uit|af|stop)?\b",
    r"\b(muziek|geluid|loop|ambient|achtergrondgeluid|natuur|vogels|vogeltjes)\s+(uit|stop|weg)\b",
    r"\b(geen|niks)\s+geluid\s*(meer)?\b",
]


# ============== TTS (text-to-speech: Spark spreekt zijn antwoord uit) ==============
TTS_ON_PATTERNS = [
    r"\btext[-\s]?to[-\s]?speech\s+(aan|aanzetten|activeren|start)\b",
    r"\btts\s+(aan|aanzetten|activeren|start)\b",
    r"\b(zet|doe)\s+(de\s+)?(tts|text[-\s]?to[-\s]?speech|stem|spraak\s*output)\s+aan\b",
    r"\bik\s+wil\s+(je|spark|hem)\s+horen\b",
    r"\b(spreek|praat)\s+(tegen\s+)?(me|mij|tegen)\b",
    r"\b(stem|spraak)\s+aan\b",
    r"\b(zet|doe)\s+(je\s+)?stem\s+aan\b",
]
TTS_OFF_PATTERNS = [
    r"\btext[-\s]?to[-\s]?speech\s+(uit|uitzetten|stoppen|stop|deactiveren)\b",
    r"\btts\s+(uit|uitzetten|stoppen|stop|deactiveren)\b",
    r"\b(zet|doe)\s+(de\s+)?(tts|text[-\s]?to[-\s]?speech|stem|spraak\s*output)\s+uit\b",
    r"\b(stop|hou\s+op)\s+(met\s+)?(praten|spreken)\b",
    r"\b(wees|ben)\s+(stil|stilletjes)\b",
    r"\b(stem|spraak)\s+uit\b",
]


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

    # 1. STT off (eerst, want "stt uit" mag niet als "stt aan" matchen)
    if _match_any(text, STT_OFF_PATTERNS):
        return {
            "action": "disable_stt",
            "message": "Speech-to-Text uitgezet. Je kunt weer typen 🌝",
            "type": "action_stt_off",
        }

    # 2. STT on
    if _match_any(text, STT_ON_PATTERNS):
        return {
            "action": "enable_stt",
            "message": "Speech-to-Text aangezet — ik luister, druk de mic-knop om in te spreken. Zeg of typ 'stt uit' om te stoppen.",
            "type": "action_stt_on",
        }

    # 2b. TTS off (vóór on)
    if _match_any(text, TTS_OFF_PATTERNS):
        return {
            "action": "disable_tts",
            "message": "Text-to-Speech uit. Ik schrijf, maar zwijg verder 🤐",
            "type": "action_tts_off",
        }

    # 2c. TTS on
    if _match_any(text, TTS_ON_PATTERNS):
        return {
            "action": "enable_tts",
            "message": "Text-to-Speech aan. Vanaf nu spreek ik mijn antwoord uit. Zeg of typ 'tts uit' om te stoppen.",
            "type": "action_tts_on",
        }

    # 3. Ambient off
    if _match_any(text, AMBIENT_OFF_PATTERNS):
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
