"""
Shadow Observer (v4_015) — Stille observator van Spark's chat-gedrag.

Doel:
  • Logt elke chat-beurt naar /data/shadow/events/YYYY-MM-DD.jsonl (append-only)
  • Houdt aggregate counters bij in /data/shadow/stats.json
  • Detecteert lichte zelf-lering-signalen: corrections, confirmations
  • Niet-blokkerend: alle fouten worden gesilenced (chat mag nooit breken)
  • Read-only voor de rest van de app — alleen de observer schrijft

Fundament voor:
  • Analyser (v4_016) — leest deze data om inzichten te geven
  • Advisor UI (v4_017) — toont insights, accepteert/wijst suggesties af
"""
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ============== PATHS ==============
SHADOW_ROOT = Path(__file__).parent.parent.parent / "data" / "shadow"
EVENTS_DIR = SHADOW_ROOT / "events"
STATS_FILE = SHADOW_ROOT / "stats.json"


def _ensure_dirs():
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)


# ============== SELF-LEARNING SIGNALS ==============
_CORRECTION_PATTERNS = [
    r"\bnee\b.*\b(klopt|bedoel|hoor)\b",
    r"\b(niet|nee).*(wat|wat ik).*\b(bedoel|zeg|vraag)\b",
    r"\bdat is (fout|verkeerd|niet juist|onjuist)\b",
    r"\b(verkeerd|fout)\b.*\b(antwoord|begrepen)\b",
    r"\b(snap je niet|begrijp je niet|snapt me niet)\b",
    r"\bdat klopt niet\b",
    r"\b(probeer opnieuw|opnieuw graag)\b",
    # v4_shadow_002 — frustratie uit productie:
    r"\bja maar\b",                                  # "Ja maar dat vroeg ik niet"
    r"\bdat vroeg ik niet\b",
    r"\bnergens voor nodig\b",                       # "Dat is nergens voor nodig"
    r"\b(loopt achter|werkt niet|doet niks)\b",     # "Je klok loopt achter"
    r"\b(waarom (word|wordt) je)\b",                # "Waarom word je boos"
    r"\b(luister je wel|hoor je me)\b",
]
_CONFIRM_PATTERNS = [
    r"\b(precies|inderdaad|klopt|exact|juist)\b",
    r"\b(goed (zo|gezien|gedaan))\b",
    r"\b(ja dat klopt|ja precies|ja inderdaad)\b",
    r"\b(top|prima|mooi (zo)?)\b",
    r"\b(dat is wat ik (bedoel|zoek))\b",
]


def _detect_signal(text: str) -> Optional[str]:
    """Return 'correction', 'confirmation' of None op basis van user text."""
    if not text:
        return None
    t = text.lower().strip()
    for pat in _CORRECTION_PATTERNS:
        if re.search(pat, t):
            return "correction"
    for pat in _CONFIRM_PATTERNS:
        if re.search(pat, t):
            return "confirmation"
    return None


# ============== STATS ==============
def _empty_stats() -> Dict[str, Any]:
    return {
        "totals": {
            "events": 0,
            "corrections": 0,
            "confirmations": 0,
            "fallbacks": 0,
            "knowledge_matches": 0,
        },
        "triggers_used": {},     # trigger_type -> count
        "response_types": {},    # response.type -> count
        "begrip_used": {},       # begrip name -> count
        "fallbacks_by_key": {},  # fallback key -> count
        "lagen_used": {},        # "laag1".."laag4" -> count
        "vocab_used": {},        # vocab key -> count
        "bijbel_used": {},       # bijbel/kernwaarde id -> count
        "last_event_at": None,
        "first_event_at": None,
    }


def _load_stats() -> Dict[str, Any]:
    if not STATS_FILE.exists():
        return _empty_stats()
    try:
        data = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        # Defensief: vul ontbrekende keys
        defaults = _empty_stats()
        for k, v in defaults.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return _empty_stats()


def _save_stats(stats: Dict[str, Any]) -> None:
    _ensure_dirs()
    tmp = STATS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, STATS_FILE)


def _inc(counter: Dict[str, int], key: Any) -> None:
    if key is None:
        return
    k = str(key)[:120]
    counter[k] = counter.get(k, 0) + 1


# ============== EVENT BUILD ==============
def _build_event(user_id: Optional[str], user_msg: str, response: Dict[str, Any], trigger_type: Any) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    # Knowledge match begrippen
    km = response.get("knowledge_matches") or []
    if isinstance(km, dict):
        km = [km]
    begrippen = [m.get("begrip") for m in km if isinstance(m, dict) and m.get("begrip")]
    # Laag
    laag = response.get("laag_used") or response.get("layer_used")
    # Fallback
    fb_key = response.get("fallback_key")
    used_fallback = bool(response.get("used_fallback") or response.get("type") == "fallback" or fb_key)
    # Vocab / bijbel
    vocab_keys = response.get("vocab_used") or []
    bijbel_ids = response.get("bijbel_used") or []
    if isinstance(vocab_keys, str):
        vocab_keys = [vocab_keys]
    if isinstance(bijbel_ids, str):
        bijbel_ids = [bijbel_ids]

    signal = _detect_signal(user_msg)

    return {
        "ts": now.isoformat(),
        "ts_epoch": now.timestamp(),
        "user_id": user_id,
        "user_msg": (user_msg or "")[:500],
        "spark_msg_preview": (response.get("message") or "")[:300],
        "trigger_type": str(trigger_type) if trigger_type is not None else None,
        "response_type": response.get("type"),
        "begrippen": begrippen[:10],
        "laag": laag,
        "used_fallback": used_fallback,
        "fallback_key": fb_key,
        "vocab_used": [str(v)[:80] for v in vocab_keys][:10],
        "bijbel_used": [str(b)[:80] for b in bijbel_ids][:10],
        "user_signal": signal,
        "unknown_words_count": len(response.get("unknown_words") or []),
    }


def _append_event(event: Dict[str, Any]) -> None:
    _ensure_dirs()
    day = event["ts"][:10]
    fpath = EVENTS_DIR / f"{day}.jsonl"
    with fpath.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _update_stats(event: Dict[str, Any]) -> None:
    stats = _load_stats()
    t = stats["totals"]
    t["events"] += 1
    if event["user_signal"] == "correction":
        t["corrections"] += 1
    elif event["user_signal"] == "confirmation":
        t["confirmations"] += 1
    if event["used_fallback"]:
        t["fallbacks"] += 1
        _inc(stats["fallbacks_by_key"], event.get("fallback_key") or "_unknown_")
    t["knowledge_matches"] += len(event.get("begrippen") or [])

    _inc(stats["triggers_used"], event.get("trigger_type"))
    _inc(stats["response_types"], event.get("response_type"))
    for b in event.get("begrippen") or []:
        _inc(stats["begrip_used"], b)
    if event.get("laag"):
        _inc(stats["lagen_used"], event["laag"])
    for v in event.get("vocab_used") or []:
        _inc(stats["vocab_used"], v)
    for b in event.get("bijbel_used") or []:
        _inc(stats["bijbel_used"], b)

    stats["last_event_at"] = event["ts"]
    if not stats.get("first_event_at"):
        stats["first_event_at"] = event["ts"]
    _save_stats(stats)


# ============== PUBLIC API ==============
def record(user_id: Optional[str], user_msg: str, response: Dict[str, Any], trigger_type: Any = None) -> None:
    """
    Niet-blokkerend logevent. Mag NOOIT chat-flow breken.
    Roep aan vanuit chat/routes._save_log.
    """
    try:
        event = _build_event(user_id, user_msg or "", response or {}, trigger_type)
        _append_event(event)
        _update_stats(event)
    except Exception:
        # Stille faal — observer mag de chat nooit blokkeren
        pass


def get_recent_events(limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Read laatste N events (laatste dag eerst)."""
    _ensure_dirs()
    files = sorted(EVENTS_DIR.glob("*.jsonl"), reverse=True)
    out: List[Dict[str, Any]] = []
    for fpath in files:
        try:
            lines = fpath.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in reversed(lines):
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if user_id and ev.get("user_id") != user_id:
                continue
            out.append(ev)
            if len(out) >= limit:
                return out
    return out


def get_stats() -> Dict[str, Any]:
    return _load_stats()


def get_unused_items() -> Dict[str, List[str]]:
    """
    Lichte zelf-lering signaal: welke triggers/vocab/bijbel-items zijn nog NOOIT gebruikt?
    Wordt later door de Analyser benut om voorstellen aan de Advisor UI te geven.

    Veilige aanpak: vergelijk JSON-bestanden met stats counters.
    """
    stats = _load_stats()
    used_triggers = set(stats.get("triggers_used", {}).keys())
    used_vocab = set(stats.get("vocab_used", {}).keys())
    used_bijbel = set(stats.get("bijbel_used", {}).keys())

    unused: Dict[str, List[str]] = {"triggers": [], "vocab": [], "bijbel": []}

    base = Path(__file__).parent.parent.parent / "data"
    # Triggers
    try:
        t = json.loads((base / "triggers" / "conversation_triggers.json").read_text(encoding="utf-8"))
        for key in (t.keys() if isinstance(t, dict) else []):
            if key not in used_triggers:
                unused["triggers"].append(key)
    except Exception:
        pass
    # Vocab
    try:
        v = json.loads((base / "personality" / "spark_vocab.json").read_text(encoding="utf-8"))
        for cat, items in (v.items() if isinstance(v, dict) else []):
            label = f"{cat}"
            if label not in used_vocab:
                unused["vocab"].append(label)
    except Exception:
        pass
    # Bijbel — kernwaarden + normen
    try:
        b = json.loads((base / "personality" / "spark_bijbel.json").read_text(encoding="utf-8"))
        if isinstance(b, dict):
            for section in ("kernwaarden", "normen", "bijbel_items"):
                for item in b.get(section) or []:
                    if isinstance(item, dict):
                        key = item.get("id") or item.get("naam") or item.get("titel")
                        if key and str(key) not in used_bijbel:
                            unused["bijbel"].append(f"{section}:{key}")
    except Exception:
        pass

    # Limiteer voor UI
    for k in unused:
        unused[k] = unused[k][:200]
    return unused


def get_correction_examples(limit: int = 20) -> List[Dict[str, Any]]:
    """Laatste momenten dat user "nee/fout" zei — input voor Analyser."""
    recent = get_recent_events(limit=500)
    out = [ev for ev in recent if ev.get("user_signal") == "correction"]
    return out[:limit]


def reset_stats() -> Dict[str, Any]:
    """Admin-only reset (events blijven staan)."""
    fresh = _empty_stats()
    _save_stats(fresh)
    return fresh
