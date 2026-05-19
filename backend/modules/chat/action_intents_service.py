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
    r"\b(stop|zet)\s+(de\s+)?(muziek|geluid|loop|ambient|achtergrondgeluid|natuur|vogels|vogeltjes)\s*(uit|af|stop)?\b",
    r"\b(muziek|geluid|loop|ambient|achtergrondgeluid|natuur|vogels|vogeltjes)\s+(uit|stop|weg)\b",
    r"\b(geen|niks)\s+geluid\s*(meer)?\b",
    r"\bambient\s+(uit|stop)\b",
]


def _load_loops():
    if not AMBIENT_REGISTRY.exists():
        return []
    try:
        return (json.loads(AMBIENT_REGISTRY.read_text()) or {}).get("loops", [])
    except Exception:
        return []


def _detect_ambient_on(text: str) -> Optional[dict]:
    """Vind een loop waarvan een trigger-woord in de tekst zit + actie-intent.
    Voorbeelden: 'vogels aan', 'zet vogels aan', 'speel vogels af', 'doe wat natuurgeluid'."""
    t = text.lower()
    action_words = [
        r"\baan\b", r"\baanzetten\b", r"\bspeel\b", r"\bafspelen\b",
        r"\bdoe\b", r"\bzet\b", r"\bstart\b", r"\bbegin\b", r"\bwil\b",
    ]
    has_action = any(re.search(p, t) for p in action_words)
    for loop in _load_loops():
        for trig in loop.get("triggers", []):
            if re.search(rf"\b{re.escape(trig.lower())}\b", t):
                # Bij directe match op trigger zonder action-woord: vraag bevestiging via toch maar wel afspelen
                # Vereisen we tenminste één action-woord OF de trigger zelf is een werkwoord ("fluiten")
                if has_action or trig.lower() in ("fluiten",):
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
