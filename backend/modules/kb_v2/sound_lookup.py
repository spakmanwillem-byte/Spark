"""
v6_kb_sound_001 — Helper om KB-kaart 'geluid'-audio op te zoeken voor een begrip.

Wordt gebruikt door chat-pipeline: wanneer user `kb_sound_enabled=True` heeft,
scan Spark's response op KB-begrippen die een geluid hebben en stuur de
audio-URL mee. Frontend speelt het af (apart van TTS).
"""
import re
import json
from pathlib import Path
from functools import lru_cache
from typing import Optional, List, Tuple

_KB_V2_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"


def _audio_for_card(card: dict) -> Optional[str]:
    """Returneer eerste 'geluid'-audio URL uit kaart, of None."""
    m = card.get("media") or {}
    # Primaire voice als kind='geluid'
    if m.get("voice_url") and (m.get("voice_kind") == "geluid"):
        return m["voice_url"]
    # Extra audio met kind='geluid'
    for a in (m.get("extra_audio") or []):
        if a.get("kind") == "geluid" and a.get("url"):
            return a["url"]
    return None


def _build_index() -> dict:
    """{begrip_lower: audio_url} — alleen kaarten die een 'geluid'-audio hebben."""
    idx = {}
    if not _KB_V2_DIR.exists():
        return idx
    files = list(_KB_V2_DIR.glob("knowledge_v2_*.json")) + [_KB_V2_DIR / "knowledge_inbox.json"]
    for f in files:
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        for k in d.get("kaarten", []):
            audio = _audio_for_card(k)
            if not audio:
                continue
            begrip = (k.get("begrip") or "").strip().lower()
            if begrip and begrip not in idx:
                idx[begrip] = audio
    return idx


# Cache van index — refresh wanneer files muteren (zie find_sound_for_text)
_INDEX_CACHE: dict = {}
_INDEX_MTIME: float = 0.0


def _index_mtime() -> float:
    """Hoogste mtime van alle KB v2 bestanden, voor cache-invalidation."""
    if not _KB_V2_DIR.exists():
        return 0.0
    mtimes = [f.stat().st_mtime for f in _KB_V2_DIR.glob("knowledge_v2_*.json")]
    inbox = _KB_V2_DIR / "knowledge_inbox.json"
    if inbox.exists():
        mtimes.append(inbox.stat().st_mtime)
    return max(mtimes) if mtimes else 0.0


def _get_index() -> dict:
    global _INDEX_CACHE, _INDEX_MTIME
    cur_mtime = _index_mtime()
    if cur_mtime > _INDEX_MTIME or not _INDEX_CACHE:
        _INDEX_CACHE = _build_index()
        _INDEX_MTIME = cur_mtime
    return _INDEX_CACHE


_WORD_RE = re.compile(r"\b[\wÀ-ÿ]+\b", re.UNICODE)


def find_sound_for_text(text: str) -> Optional[Tuple[str, str]]:
    """
    Zoek eerste KB-begrip met 'geluid' in `text`.
    Returneert (begrip, audio_url) of None.
    """
    if not text:
        return None
    idx = _get_index()
    if not idx:
        return None
    # Tokeniseer + zoek per woord (exact match op begrip — KB v2 begrippen zijn meestal 1 woord)
    seen = set()
    for m in _WORD_RE.finditer(text.lower()):
        w = m.group(0)
        if w in seen:
            continue
        seen.add(w)
        if w in idx:
            return (w, idx[w])
    # Ook multi-woord begrippen (bv. "high score") proberen — exhaustive over alle KB-keys
    text_low = " " + text.lower() + " "
    for begrip, url in idx.items():
        if " " in begrip and f" {begrip} " in text_low:
            return (begrip, url)
    return None


def get_sound_for_begrip(begrip: str) -> Optional[str]:
    """Directe lookup: returneer geluid-URL voor een specifiek begrip."""
    if not begrip:
        return None
    return _get_index().get(begrip.strip().lower())


def list_indexed_begrippen() -> List[str]:
    """Debug: lijst alle begrippen met geluid."""
    return sorted(_get_index().keys())
