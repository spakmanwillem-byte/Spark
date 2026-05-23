"""
KB v2 — NLP/Vocab/Commands Hooks (v5_kbv2_hooks_001)
=====================================================

PLACEHOLDER-laag voor toekomstige aansluiting van v2-kaarten op:
  • Spark NLP (intent_matcher, smart_intents)
  • Vocab register (woorden die Spark "actief" mag gebruiken)
  • Chat-commands ("zoek in kennis: X", "leer woord: Y", "vertel diep over Z")
  • D&D Knowledge Cards (lore_index + cards-as-content)
  • Auto-graph-edges (verbanden tussen kaarten via shared tags)

🎯 DOEL: een toekomstige agent (of ik na geheugen-reset) ziet hier EXACT
   waar hooks moeten worden ingebouwd — geen zoeken, geen gokken.

🛡️ STATUS: alle functies returnen veilige defaults (None/lege lijst).
   Bij implementatie: vul de TODO-blokken in. De aanroepers veranderen NIET.

Verwijst naar:
  - MISSION.md → graceful degradation / autonomie-versterking
  - ROADMAP.md → P1: "Spark's hands", "Vocab terug van v1"
"""
from typing import List, Dict, Optional, Tuple

from modules.core.spark_logger import log_event
from . import service as kbv2

# ---------------------------------------------------------------------------
# HOOK 1: Card → Vocab register
# ---------------------------------------------------------------------------
# Wanneer een kaart in een lade staat met laag1 ingevuld, mag Spark het
# begrip "actief" gebruiken in zijn antwoorden. Dit hook leest de KB v2 en
# returnt de vocab-set per lade. Sluit later aan op `spark_vocab.json` als
# leertree.
#
# TODO (P1):
#   1. Bij elke classify_card() in service.py → call register_in_vocab()
#   2. Vocab-file: /data/personality/spark_vocab.json met velden:
#        { "vocab": { "<begrip>": {"lade": "voelen", "kaart_id": "kbv2-xxx",
#          "active": true, "first_seen": "...", "use_count": 0 }}}
#   3. spark_brain bij response-generatie: alleen `active=true` woorden
#      mag hij "spontaan" gebruiken, anders alleen reactief op user input.
# ---------------------------------------------------------------------------

def register_in_vocab(card: Dict) -> bool:
    """Hook: registreer kaart-begrip in vocab. (TODO)"""
    log_event("kbv2_hooks", "register_in_vocab",
              intent="Vocab-koppeling (placeholder)",
              detail={"begrip": card.get("begrip"), "lade": card.get("lade")})
    return False  # → True wanneer geïmplementeerd


def get_active_vocab(lade: Optional[str] = None) -> List[str]:
    """Hook: returnt lijst van actieve begrippen (voor Spark's spontane spraak). (TODO)"""
    return []


# ---------------------------------------------------------------------------
# HOOK 2: Chat-commands die KB v2 aanroepen
# ---------------------------------------------------------------------------
# Toekomstige natuurlijke commands die Spark in /chat/message moet herkennen
# en doorrouten naar v2-service:
#
#   "zoek in kennis: X"           → kbv2.find_by_begrip(X)
#   "vertel kort over X"          → laag1
#   "vertel meer / dieper over X" → laag2/3/4
#   "wat ken je over X"           → kbv2.graceful_fallback(X)
#   "leer woord: X"               → kbv2.add_to_inbox(X)
#   "noteer X is een ..."         → auto-fill laag1 via inbox/add
#
# TODO (P1):
#   1. Maak `chat/commands_kbv2.py` met match-functies (regex/fuzzy)
#   2. Hook in `chat/routes.process_message` VÓÓR de huidige snap-lookup
#      (zoals smart_intents nu al doet voor topic-overview)
#   3. Sla command-resultaten op in `last_kbv2_card_id` in session_state
#      voor follow-up vragen ("en wat nog meer over die kaart?")
# ---------------------------------------------------------------------------

# Command-registry: text-trigger → handler-naam (handler = nog te bouwen)
KBV2_CHAT_COMMANDS: List[Dict] = [
    {"id": "search_kb",   "triggers": ["zoek in kennis", "wat staat er over", "wat weet je van"],   "handler": "cmd_search_kb"},
    {"id": "tell_short",  "triggers": ["vertel kort over", "in 1 zin", "samenvatting van"],          "handler": "cmd_tell_layer"},
    {"id": "tell_deep",   "triggers": ["vertel diep over", "leg uit", "vertel meer over"],          "handler": "cmd_tell_layer"},
    {"id": "learn_word",  "triggers": ["leer woord", "onthoud dit woord", "voeg toe aan kennis"],   "handler": "cmd_learn_word"},
    {"id": "list_inbox",  "triggers": ["wat staat in inbox", "welke kaarten wachten", "hoeveel onbeantwoord"], "handler": "cmd_list_inbox"},
    {"id": "audit_kb",    "triggers": ["audit kennis", "scan kennis", "wat mist"],                  "handler": "cmd_audit_kb"},
]


def match_kbv2_command(user_text: str) -> Optional[Tuple[Dict, str]]:
    """Hook: matcht user-text tegen KBV2_CHAT_COMMANDS triggers.
    Returnt (command_dict, extracted_query) of None. (TODO: implementeer regex/fuzzy)"""
    if not user_text:
        return None
    txt = user_text.lower().strip()
    for cmd in KBV2_CHAT_COMMANDS:
        for trig in cmd["triggers"]:
            if trig in txt:
                # Extract de "query" (alles ná de trigger)
                idx = txt.index(trig) + len(trig)
                query = user_text[idx:].strip(" :,.?!").strip()
                return cmd, query
    return None


# Handlers — placeholders. Roep service.* voor de echte logica.

def cmd_search_kb(query: str) -> Dict:
    """Handler: "zoek in kennis: X" → directe lookup of fallback."""
    if not query:
        return {"type": "kbv2_cmd_empty", "message": "Wat zal ik in mijn kennis zoeken?"}
    fb = kbv2.graceful_fallback(query)
    if not fb:
        return {"type": "kbv2_cmd_miss",
                "message": f"Ik ken **{query}** nog niet. Wil je dat ik 'm leer? (zeg: leer woord {query})"}
    kaart = fb["kaart"]
    return {
        "type": f"kbv2_cmd_{fb['type']}",
        "message": f"**{kaart['begrip']}** (lade: {fb['lade']}): {(kaart.get('lagen') or {}).get('laag1','')}",
        "kbv2_card_id": kaart["id"],
    }


def cmd_tell_layer(query: str, depth: int = 1) -> Dict:
    """Handler: "vertel kort/diep over X" → laag1 of laag3/4. (TODO: depth-router)"""
    return cmd_search_kb(query)


def cmd_learn_word(query: str, user_id: str = "user-000") -> Dict:
    """Handler: "leer woord: X" → kbv2.add_to_inbox."""
    if not query:
        return {"type": "kbv2_cmd_empty", "message": "Welk woord wil je dat ik leer?"}
    r = kbv2.add_to_inbox(query, source="chat_command", user_id=user_id)
    if r.get("existing"):
        return {"type": "kbv2_cmd_known",
                "message": f"Ik kende **{query}** al — staat in lade **{r.get('lade') or 'inbox'}**."}
    return {"type": "kbv2_cmd_learned",
            "message": f"Genoteerd: **{query}** staat nu in mijn Inbox. Wil je 'm samen invullen?"}


def cmd_list_inbox(query: str = "") -> Dict:
    """Handler: 'wat staat in inbox' → samenvatting."""
    stats = kbv2.get_stats()
    n = stats.get("inbox_count", 0)
    return {
        "type": "kbv2_cmd_inbox",
        "message": f"Er staan **{n}** kaarten in mijn Inbox. Open de Kennisbank-tab om ze in te delen.",
        "inbox_count": n,
    }


def cmd_audit_kb(query: str = "") -> Dict:
    """Handler: 'audit kennis' → samenvatting van gaten."""
    a = kbv2.audit()
    s = a.get("summary", {})
    msg = (
        f"Self-audit: **{s.get('inbox_missing_laag1', 0)}** kaarten zonder laag1, "
        f"**{s.get('inbox_ties', 0)}** met tag-tie, "
        f"**{s.get('low_confidence_count', 0)}** met laag vertrouwen."
    )
    return {"type": "kbv2_cmd_audit", "message": msg, "audit": s}


# ---------------------------------------------------------------------------
# HOOK 3: Auto-graph (verbanden tussen kaarten via shared tags)
# ---------------------------------------------------------------------------
# Bestaande /data/graph/edges.json heeft 29468 edges uit v1. v2-kaarten
# hebben veld `verbanden: []` dat nog leeg is. Hook: bouw verbanden door
# kaarten met N+ overlappende tags te linken.
#
# TODO (P2):
#   1. Periodiek (1x per dag of bij classify) scan alle lades
#   2. Voor elke kaart: vind top-5 kaarten met meeste shared tags
#   3. Schrijf naar card["verbanden"] in v2-files
#   4. UI: toon "Gerelateerd:" sectie in CardDetail met click-through
# ---------------------------------------------------------------------------

def compute_verbanden(card: Dict, min_overlap: int = 3, top_n: int = 5) -> List[str]:
    """Hook: vind related cards via shared tags. (TODO)"""
    return []


# ---------------------------------------------------------------------------
# HOOK 4: D&D Knowledge Cards (Lore-as-data integratie)
# ---------------------------------------------------------------------------
# Willem's wens: kennis-kaarten = grondvorm voor D&D content (lore, items,
# inventory). Een kaart in lade `weten` met tag "lore" kan een D&D-feature
# triggeren (perk, item, achievement).
#
# TODO (P2):
#   1. Nieuwe optionele velden in card-schema:
#        "dnd": { "type": "perk"|"item"|"lore", "trigger": "...", "unlocks": [...] }
#   2. Bij classify naar lade `weten` + tag "lore" → DNDService.register(card)
#   3. lore_index.json synct van v2-cards met `dnd.type == "lore"`
# ---------------------------------------------------------------------------

def link_to_dnd(card: Dict) -> Optional[Dict]:
    """Hook: koppel kaart aan D&D-systeem indien relevant. (TODO)"""
    return None


# ---------------------------------------------------------------------------
# HOOK 5: Dialogen-archief (auto-snippet bij voice-transcript)
# ---------------------------------------------------------------------------
# Wanneer user een kaart inspreekt via /api/kb/v2/media/voice, bewaar de
# transcriptie ook als snippet in /data/dialogen/ zodat Spark's gesprek-
# stijl meegroeit met Willem's stem (zie sessie 4 finish-suggestie).
#
# TODO (P3):
#   1. In media_routes.upload_voice na succesvolle transcriptie:
#      call save_voice_snippet(transcript, card_id, user_id)
#   2. Save naar /data/dialogen/voice_snippets/YYYY-MM-DD/{card_id}_{uuid}.json
#      met velden: text, source, card_link, ingesproken_door, datum
# ---------------------------------------------------------------------------

def save_voice_snippet(transcript: str, card_id: str, user_id: str) -> bool:
    """Hook: bewaar voice-transcriptie als training-snippet. (TODO)"""
    return False
