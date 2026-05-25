"""
KB v2 — NLP/Vocab/Commands Hooks (v5_kbv2_hooks_001 + v6_kbv2_hooks_landing_001)
================================================================================

5 P1-hooks zijn nu LIVE (sessie 11):
  1. register_in_vocab     → /data/personality/spark_vocab.json
  2. cmd_tell_layer        → depth-router (laag1/2/3/4) + session-state
  3. compute_verbanden     → top-5 related cards via shared tags → kaart['verbanden']
  4. link_to_dnd           → optionele dnd:{type,trigger,unlocks} → lore_index sync
  5. save_voice_snippet    → /data/dialogen/voice_snippets/YYYY-MM-DD/

🛡️ Alle hooks zijn idempotent + falen niet hard (try/except in callers).
🧾 Elke fire schrijft een entry in `card.footnote.hooks_fired[]` voor
    toekomstige traceability (zonder logs te hoeven scannen).

Verwijst naar:
  - MISSION.md → graceful degradation / autonomie-versterking
  - ROADMAP.md → P1: "Spark's hands", "Vocab terug van v1", verbanden, D&D-link
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import uuid

from modules.core.spark_logger import log_event
from modules.core.storage import load_json, save_json
from . import service as kbv2

# ---------------------------------------------------------------------------
# Footnote-meta helper — universele tracer per kaart-mutation
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def track_hook_in_card(card: Dict, hook_name: str, result_summary: Optional[Dict] = None) -> None:
    """v6_kbv2_hooks_landing_001 — voeg hook-fire toe aan footnote.hooks_fired[].
    MUTEERT de card in-place. Caller moet zelf save_json doen."""
    if not isinstance(card, dict):
        return
    fn = card.setdefault("footnote", {})
    trail = fn.setdefault("hooks_fired", [])
    trail.append({
        "hook": hook_name,
        "fired_at": _now_iso(),
        "result": (result_summary or {}),
    })
    # Houd trail beperkt tot laatste 25 entries om bestanden klein te houden
    if len(trail) > 25:
        del trail[:-25]


# ---------------------------------------------------------------------------
# HOOK 1: Card → Vocab register
# ---------------------------------------------------------------------------
# Bij elke classify_card() of edit_card() in service.py wordt het begrip
# in /data/personality/spark_vocab.json bijgehouden. Spark's brain mag
# alleen `active=true` woorden spontaan inzetten in antwoorden.
# ---------------------------------------------------------------------------

VOCAB_FILE = Path(__file__).parent.parent.parent / "data" / "personality" / "spark_vocab.json"


def register_in_vocab(card: Dict) -> bool:
    """Schrijf begrip naar spark_vocab.json. Idempotent: update bestaande entry.
    Returns True als nieuwe entry, False bij update of skip."""
    begrip = (card.get("begrip") or "").strip()
    if not begrip:
        return False
    lade = card.get("lade") or "inbox"
    lagen = card.get("lagen") or {}
    has_laag1 = bool((lagen.get("laag1") or "").strip())
    # Active wanneer kaart in een lade staat EN laag1 gevuld is.
    # Inbox-kaarten zonder laag1 → passive (kennen het woord, gebruik niet spontaan).
    active = (lade != "inbox") and has_laag1

    VOCAB_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(VOCAB_FILE, default={"vocab": {}, "version": "v1"})
    vocab = data.setdefault("vocab", {})
    key = begrip.lower()
    now = _now_iso()
    is_new = key not in vocab
    entry = vocab.get(key) or {
        "begrip": begrip,
        "kaart_id": card.get("id"),
        "lade": lade,
        "active": active,
        "first_seen": now,
        "last_seen": now,
        "use_count": 0,
    }
    # update
    entry["kaart_id"] = card.get("id")
    entry["lade"] = lade
    entry["active"] = active
    entry["last_seen"] = now
    vocab[key] = entry
    save_json(VOCAB_FILE, data)

    log_event("kbv2_hooks", "register_in_vocab",
              intent="vocab-koppeling",
              detail={"begrip": begrip, "lade": lade, "active": active, "is_new": is_new})
    track_hook_in_card(card, "register_in_vocab",
                       {"active": active, "is_new": is_new})
    return is_new


def get_active_vocab(lade: Optional[str] = None) -> List[str]:
    """Lijst van actieve begrippen (voor Spark's spontane spraak)."""
    data = load_json(VOCAB_FILE, default={"vocab": {}})
    out = []
    for key, v in data.get("vocab", {}).items():
        if not v.get("active"):
            continue
        if lade and v.get("lade") != lade:
            continue
        out.append(v.get("begrip", key))
    return out


def bump_vocab_use_count(begrip: str) -> None:
    """Tel mee hoe vaak Spark een vocab-woord gebruikt (toekomst: ranking)."""
    if not begrip:
        return
    data = load_json(VOCAB_FILE, default={"vocab": {}})
    key = begrip.lower().strip()
    if key in data.get("vocab", {}):
        data["vocab"][key]["use_count"] = data["vocab"][key].get("use_count", 0) + 1
        data["vocab"][key]["last_used"] = _now_iso()
        save_json(VOCAB_FILE, data)


# ---------------------------------------------------------------------------
# HOOK 2: Chat-commands die KB v2 aanroepen
# ---------------------------------------------------------------------------
# Toekomstige natuurlijke commands (zie KBV2_CHAT_COMMANDS) routed naar
# v2-service. cmd_tell_layer met depth-arg leest de juiste laag.
# ---------------------------------------------------------------------------

KBV2_CHAT_COMMANDS: list = [
    {"id": "search_kb",   "triggers": ["zoek in kennis", "wat staat er over", "wat weet je van"],   "handler": "cmd_search_kb"},
    {"id": "tell_short",  "triggers": ["vertel kort over", "in 1 zin", "samenvatting van", "korte uitleg"],
                          "handler": "cmd_tell_layer", "depth": 1},
    {"id": "tell_more",   "triggers": ["vertel meer over", "leg uit", "beschrijf"],
                          "handler": "cmd_tell_layer", "depth": 2},
    {"id": "tell_deep",   "triggers": ["vertel diep over", "vertel alles over", "diep uitleg"],
                          "handler": "cmd_tell_layer", "depth": 3},
    {"id": "tell_full",   "triggers": ["vertel volledig over", "alles wat je weet over"],
                          "handler": "cmd_tell_layer", "depth": 4},
    {"id": "learn_word",  "triggers": ["leer woord", "onthoud dit woord", "voeg toe aan kennis"],   "handler": "cmd_learn_word"},
    {"id": "list_inbox",  "triggers": ["wat staat in inbox", "welke kaarten wachten", "hoeveel onbeantwoord"], "handler": "cmd_list_inbox"},
    {"id": "audit_kb",    "triggers": ["audit kennis", "scan kennis", "wat mist"],                  "handler": "cmd_audit_kb"},
    # v5_card_factory_001 — game-kaart commands
    {"id": "make_dnd",    "triggers": ["maak een d&d kaart", "maak dnd kaart", "nieuwe dnd kaart"],
                          "handler": "cmd_make_card", "card_type": "dnd"},
    {"id": "make_event",  "triggers": ["maak een event kaart", "nieuw event", "maak event"],
                          "handler": "cmd_make_card", "card_type": "event"},
    {"id": "make_bark",   "triggers": ["maak een bark kaart", "nieuwe bark", "maak bark"],
                          "handler": "cmd_make_card", "card_type": "bark"},
]


def match_kbv2_command(user_text: str) -> Optional[Tuple[Dict, str]]:
    """Matcht user-text tegen KBV2_CHAT_COMMANDS triggers.
    Returnt (command_dict, extracted_query) of None."""
    if not user_text:
        return None
    txt = user_text.lower().strip()
    for cmd in KBV2_CHAT_COMMANDS:
        for trig in cmd["triggers"]:
            if trig in txt:
                idx = txt.index(trig) + len(trig)
                query = user_text[idx:].strip(" :,.?!").strip()
                return cmd, query
    return None


def cmd_search_kb(query: str) -> Dict:
    """"zoek in kennis: X" → directe lookup of fallback."""
    if not query:
        return {"type": "kbv2_cmd_empty", "message": "Wat zal ik in mijn kennis zoeken?"}
    fb = kbv2.graceful_fallback(query)
    if not fb:
        return {"type": "kbv2_cmd_miss",
                "message": f"Ik ken **{query}** nog niet. Wil je dat ik 'm leer? (zeg: leer woord {query})"}
    kaart = fb["kaart"]
    bump_vocab_use_count(kaart.get("begrip", ""))
    return {
        "type": f"kbv2_cmd_{fb['type']}",
        "message": f"**{kaart['begrip']}** (lade: {fb['lade']}): {(kaart.get('lagen') or {}).get('laag1','')}",
        "kbv2_card_id": kaart["id"],
        "kbv2_lade": fb["lade"],
    }


def cmd_tell_layer(query: str, depth: int = 1) -> Dict:
    """v6_kbv2_hooks_landing_001 — depth-router: laag1 (kort) / 2 (meer) / 3 (diep) / 4 (volledig).
    Bouwt antwoord op uit alle gevraagde lagen + valt terug bij missing laag."""
    if not query:
        return {"type": "kbv2_cmd_empty", "message": "Over welk begrip wil je dat ik vertel?"}
    fb = kbv2.graceful_fallback(query)
    if not fb or fb.get("type") != "direct":
        # Geen direct hit → val terug op search-result + suggestie
        return cmd_search_kb(query)
    kaart = fb["kaart"]
    lagen = kaart.get("lagen") or {}
    depth = max(1, min(4, int(depth)))
    bump_vocab_use_count(kaart.get("begrip", ""))

    parts = []
    # Bouw cumulatief op tot het gevraagde diepte-niveau
    used_layers = []
    for i in range(1, depth + 1):
        v = (lagen.get(f"laag{i}") or "").strip()
        if v:
            parts.append(v)
            used_layers.append(f"laag{i}")
    if not parts:
        return {
            "type": "kbv2_cmd_no_content",
            "message": f"Ik ken **{kaart['begrip']}** wel, maar de gewenste laag is nog leeg. Wil je 'm aanvullen?",
            "kbv2_card_id": kaart["id"],
        }

    label = {1: "kort", 2: "meer", 3: "diep", 4: "volledig"}[depth]
    body = "\n\n".join(parts)
    return {
        "type": f"kbv2_tell_{label}",
        "message": f"**{kaart['begrip']}** _(lade: {fb['lade']}, {label})_:\n\n{body}",
        "kbv2_card_id": kaart["id"],
        "kbv2_lade": fb["lade"],
        "kbv2_depth": depth,
        "kbv2_layers_used": used_layers,
    }


def cmd_learn_word(query: str, user_id: str = "user-000") -> Dict:
    """"leer woord: X" → kbv2.add_to_inbox."""
    if not query:
        return {"type": "kbv2_cmd_empty", "message": "Welk woord wil je dat ik leer?"}
    r = kbv2.add_to_inbox(query, source="chat_command", user_id=user_id)
    if r.get("existing"):
        return {"type": "kbv2_cmd_known",
                "message": f"Ik kende **{query}** al — staat in lade **{r.get('lade') or 'inbox'}**.",
                "kbv2_card_id": r.get("kaart", {}).get("id")}
    return {"type": "kbv2_cmd_learned",
            "message": f"Genoteerd: **{query}** staat nu in mijn Inbox. Wil je 'm samen invullen?",
            "kbv2_card_id": r.get("kaart", {}).get("id")}


def cmd_list_inbox(query: str = "") -> Dict:
    """'wat staat in inbox' → samenvatting."""
    stats = kbv2.get_stats()
    n = stats.get("inbox_count", 0)
    return {
        "type": "kbv2_cmd_inbox",
        "message": f"Er staan **{n}** kaarten in mijn Inbox. Open de Kennisbank-tab om ze in te delen.",
        "inbox_count": n,
    }


def cmd_audit_kb(query: str = "") -> Dict:
    """'audit kennis' → samenvatting van gaten."""
    a = kbv2.audit()
    s = a.get("summary", {})
    msg = (
        f"Self-audit: **{s.get('inbox_missing_laag1', 0)}** kaarten zonder laag1, "
        f"**{s.get('inbox_ties', 0)}** met tag-tie, "
        f"**{s.get('low_confidence_count', 0)}** met laag vertrouwen."
    )
    return {"type": "kbv2_cmd_audit", "message": msg, "audit": s}


def cmd_make_card(query: str, user_id: str = "user-000", card_type: str = "dnd") -> Dict:
    """'maak een D&D kaart' / 'maak event kaart' / 'maak bark kaart'."""
    from modules.cards import service as cards_service
    titel = (query or f"Nieuwe {card_type}-kaart").strip()
    r = cards_service.create_card(card_type, titel=titel, user_id=user_id)
    if not r.get("success"):
        return {"type": "card_factory_error", "message": r.get("message", "Aanmaken mislukt")}
    card = r["card"]
    return {
        "type": f"card_made_{card_type}",
        "message": (
            f"🃏 **{card_type.upper()}-kaart aangemaakt**: _{card['titel']}_\n\n"
            f"ID: `{card['id']}` (draft)\n\n"
            f"Nu kun je:\n"
            f"• Een **vraag** of **antwoord** invullen (1 van 2 is genoeg om kaart actief te maken)\n"
            f"• Een **afbeelding** of **geluid** uploaden via Beheer→Kaarten\n"
            f"• Tags toevoegen voor categorisering\n\n"
            f"Endpoint: `POST /api/cards/{card_type}/{card['id']}`"
        ),
        "card_id": card["id"],
        "card_type": card_type,
    }


# ---------------------------------------------------------------------------
# HOOK 3: Auto-graph (verbanden tussen kaarten via shared tags)
# ---------------------------------------------------------------------------

def compute_verbanden(card: Dict, min_overlap: int = 2, top_n: int = 5) -> List[Dict]:
    """v6_kbv2_hooks_landing_001 — vind top-N kaarten met meeste shared tags.
    Schrijft NIET zelf naar disk; caller (classify/edit) doet save.
    Returnt lijst van {kaart_id, begrip, lade, overlap}."""
    own_tags = {(t or "").lower() for t in (card.get("tags") or []) if t}
    if len(own_tags) < min_overlap:
        return []
    own_id = card.get("id")
    candidates = []
    for lade in kbv2.LADES:
        d = load_json(kbv2._lade_path(lade), default={"kaarten": []})
        for k in d.get("kaarten", []):
            if k.get("id") == own_id:
                continue
            tags = {(t or "").lower() for t in (k.get("tags") or []) if t}
            ov = own_tags & tags
            if len(ov) >= min_overlap:
                candidates.append({
                    "kaart_id": k.get("id"),
                    "begrip": k.get("begrip", ""),
                    "lade": lade,
                    "overlap": len(ov),
                    "shared_tags": sorted(list(ov))[:5],
                })
    candidates.sort(key=lambda x: x["overlap"], reverse=True)
    top = candidates[:top_n]
    if top:
        track_hook_in_card(card, "compute_verbanden",
                           {"n_found": len(top), "top_overlap": top[0]["overlap"]})
        log_event("kbv2_hooks", "compute_verbanden",
                  intent="verbanden-graph",
                  detail={"begrip": card.get("begrip"), "found": len(top)})
    return top


# ---------------------------------------------------------------------------
# HOOK 4: D&D Knowledge Cards (Lore-as-data integratie)
# ---------------------------------------------------------------------------

LORE_INDEX_FILE = Path(__file__).parent.parent.parent / "data" / "dnd" / "lore_index.json"


def link_to_dnd(card: Dict) -> Optional[Dict]:
    """v6_kbv2_hooks_landing_001 — als kaart D&D-relevante tags heeft (lore/dnd/spark world),
    voeg 'm toe aan lore_index als type=lore. Idempotent op kaart-id."""
    tags = [(t or "").lower() for t in (card.get("tags") or [])]
    lore_triggers = {"lore", "dnd", "d&d", "spark world", "base line"}
    has_lore = any(t in lore_triggers for t in tags)
    has_explicit = isinstance(card.get("dnd"), dict)
    if not (has_lore or has_explicit):
        return None

    LORE_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    idx = load_json(LORE_INDEX_FILE, default={"version": "v1", "lore": []})
    lore_list = idx.setdefault("lore", [])
    own_id = card.get("id")
    existing = next((x for x in lore_list if x.get("kbv2_card_id") == own_id), None)
    dnd_meta = card.get("dnd") if isinstance(card.get("dnd"), dict) else {}
    entry = {
        "kbv2_card_id": own_id,
        "begrip": card.get("begrip", ""),
        "lade": card.get("lade") or "inbox",
        "type": dnd_meta.get("type", "lore"),
        "trigger": dnd_meta.get("trigger"),
        "unlocks": dnd_meta.get("unlocks", []),
        "tags": tags,
        "linked_at": _now_iso(),
    }
    if existing:
        existing.update(entry)
        action = "updated"
    else:
        lore_list.append(entry)
        action = "added"
    save_json(LORE_INDEX_FILE, idx)
    track_hook_in_card(card, "link_to_dnd",
                       {"action": action, "type": entry["type"]})
    log_event("kbv2_hooks", "link_to_dnd",
              intent="lore-koppeling",
              detail={"begrip": card.get("begrip"), "action": action})
    return entry


# ---------------------------------------------------------------------------
# HOOK 5: Dialogen-archief (auto-snippet bij voice-transcript)
# ---------------------------------------------------------------------------

VOICE_SNIPPETS_DIR = Path(__file__).parent.parent.parent / "data" / "dialogen" / "voice_snippets"


def save_voice_snippet(transcript: str, card_id: str, user_id: str,
                       voice_url: Optional[str] = None) -> bool:
    """v6_kbv2_hooks_landing_001 — bewaar Whisper-transcriptie als dialoog-snippet.
    Per-dag map zodat Spark's stem-stijl traceerbaar groeit met Willem's input."""
    transcript = (transcript or "").strip()
    if not transcript:
        return False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_dir = VOICE_SNIPPETS_DIR / today
    day_dir.mkdir(parents=True, exist_ok=True)
    snippet_id = uuid.uuid4().hex[:10]
    snippet_path = day_dir / f"{card_id}_{snippet_id}.json"
    snippet = {
        "id": snippet_id,
        "card_id": card_id,
        "transcript": transcript,
        "voice_url": voice_url,
        "ingesproken_door": user_id,
        "datum": today,
        "created_at": _now_iso(),
        "source": "kbv2_voice_upload",
        # Footnote-meta voor toekomst: koppel terug naar kaart + run-context
        "footnote": {
            "module": "kbv2_hooks.save_voice_snippet",
            "kbv2_card_id": card_id,
            "user_id": user_id,
        },
    }
    save_json(snippet_path, snippet)
    log_event("kbv2_hooks", "save_voice_snippet",
              intent="dialoog-snippet bewaard",
              detail={"card_id": card_id, "chars": len(transcript), "date": today})
    return True
