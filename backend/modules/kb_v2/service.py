"""
Knowledge Base v2 Service (v5_kbv2_001)
========================================
Read/write toegang tot de 4 lades + inbox + index van KB v2.

Architectuur (zie ARCHITECTURE.md → Laag 3: Geheugen):

  knowledge_v2_voelen.json     🌸  emotie/verbinding
  knowledge_v2_spreken.json    💬  taal/dialoog
  knowledge_v2_weten.json      🧠  kennis/systeem
  knowledge_v2_doen.json       🎭  gedrag/actie
  knowledge_inbox.json         📥  onbeantwoord/tie/no-match
  knowledge_index.json         🗂️  begrip → {lade, kaart_id, has_lagen}
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json
from modules.core.spark_logger import traced, log_event

V2_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"

LADES = ["voelen", "spreken", "weten", "doen", "games"]

LADE_META = {
    "voelen": {"icon": "🌸", "naam": "Voelen", "stroom": "Emotie & Verbinding"},
    "spreken": {"icon": "💬", "naam": "Spreken", "stroom": "Communicatie & Taal"},
    "weten": {"icon": "🧠", "naam": "Weten", "stroom": "Systeem & Kennis"},
    "doen": {"icon": "🎭", "naam": "Doen", "stroom": "Gedrag & Actie"},
    "games": {"icon": "🎮", "naam": "Spark Games", "stroom": "Spel & Wereld", "realiteit": "fictie"},
}

# v14_fictie_gate_001 (Willem 17-09-2026): "spark moet geen fantoom krijgen met realiteit".
# Kaarten in fictie-lades (Spark World) zijn kennis vóór Spark, maar mogen alleen
# meedoen in een antwoord als de user het over de game heeft.
FICTIE_LADES = {"games"}

# v14_min_tags_001 (Willem 17-09-2026): "zonder tags kan hij niet naar een lade en blijft in
# algemene inbox; alles moet minimaal 5 tags hebben voor goedkeuring."
MIN_TAGS_FOR_LADE = 5


def tags_gate(tags) -> Optional[str]:
    """None als OK, anders de weigerreden."""
    n = len([t for t in (tags or []) if str(t).strip()])
    if n < MIN_TAGS_FOR_LADE:
        return f"Te weinig tags ({n}/{MIN_TAGS_FOR_LADE}) — kaart blijft in inbox tot er minimaal {MIN_TAGS_FOR_LADE} tags zijn"
    return None
_GAME_CONTEXT_WORDS = (
    "spark world", "spark games", "game", "spel", "spelen", "speler", "fractie", "fracties",
    "base line", "persoonskaart", "rugzak", "inventory", "grondstof", "lore", "sandbox",
)


def is_game_context(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in _GAME_CONTEXT_WORDS)


def filter_fictie(cards: List[Dict], query: str, lade_key: str = "_lade") -> List[Dict]:
    """Verwijder fictie-kaarten uit een resultaat tenzij de vraag over de game gaat."""
    if is_game_context(query):
        return cards
    return [c for c in cards if (c.get(lade_key) or c.get("lade")) not in FICTIE_LADES]

_lock = threading.RLock()


def _lade_path(lade: str) -> Path:
    return V2_DIR / f"knowledge_v2_{lade}.json"


def _inbox_path() -> Path:
    return V2_DIR / "knowledge_inbox.json"


def _index_path() -> Path:
    return V2_DIR / "knowledge_index.json"


# v13_kbv2_inbox_dedupe_002 — Willem 2026-08-27:
# "Ik zag dubbele kaarten in Inbox — begrip dat ik al eerder ingevuld had."
# Root cause: knowledge_index.json kan stale zijn, waardoor add_to_inbox()
# geen dubbel-detectie doet en een lege kaart naast de gevulde lade-kaart
# neerzet. Deze helper doet een DEEP-scan over de 4 lade-bestanden en
# retourneert een set van begrippen die daar met een gevulde laag1 staan.
# Wordt gebruikt door list_inbox (soft-filter zonder data te muteren) en
# door add_to_inbox (harde weiger + auto-repair index).
def _begrippen_filled_in_lades() -> Dict[str, tuple]:
    """Returns dict begrip.lower() → (lade, kaart_id) voor kaarten met gevulde laag1."""
    result: Dict[str, tuple] = {}
    for L in LADES:
        d = load_json(_lade_path(L), default={"kaarten": []})
        for k in d.get("kaarten", []):
            b = (k.get("begrip") or "").lower().strip()
            l1 = (k.get("lagen", {}) or {}).get("laag1", "") if isinstance(k.get("lagen"), dict) else ""
            if b and (l1 or "").strip():
                # Eerst-gevonden wint bij dubbels in verschillende lades (self-heal via dedupe)
                result.setdefault(b, (L, k.get("id")))
    return result



def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compute_needs(card: Dict) -> list:
    """Wat mist deze kaart nog? Gebruikt door UI-checklist."""
    needs = []
    lagen = card.get("lagen") or {}
    if not (lagen.get("laag1") or "").strip():
        needs.append("laag1")
    if not any((card.get("ws5") or {}).values()):
        needs.append("ws5")
    media = card.get("media") or {}
    if not media.get("voice_url"):
        needs.append("voice")
    if not (media.get("image_urls") or []):
        needs.append("image")
    return needs


# ---------------------------------------------------------------------------
# Read API
# ---------------------------------------------------------------------------

def get_stats() -> Dict:
    """Snelle stats over alle 4 lades + inbox."""
    stats = {"lades": {}, "inbox_count": 0, "total": 0}
    for lade in LADES:
        d = load_json(_lade_path(lade), default={"kaarten": []})
        n = len(d.get("kaarten", []))
        stats["lades"][lade] = {
            **LADE_META[lade],
            "count": n,
        }
        stats["total"] += n
    inbox = load_json(_inbox_path(), default={"kaarten": []})
    stats["inbox_count"] = len(inbox.get("kaarten", []))
    stats["total"] += stats["inbox_count"]
    return stats


# ---------------------------------------------------------------------------
# Semantic Lookup — v13_semantic_lookup_001 (Spark zelfbewust laten worden)
#
# Filosofie (Willem, sessie 53): Spark heeft 6000+ kaarten met 5W-gevulde
# betekenissen. Voorheen zocht `list_lade`/`list_inbox` alleen in `begrip`
# (regel 1 van de kaart). Effect: al Willem's 5W-werk lag in de kluis maar
# Spark las alleen het opschrift. Deze lookup opent alle velden en scoort met
# gewichten zodat een chat-vraag matcht op de vólle inhoud.
#
# Ranking (in aflopend gewicht):
#   +10  match in `begrip` (hoofd-concept)
#   + 5  match in `ws5.{wie,wat,waar,wanneer,waarom}` waarden
#   + 3  match in `tags`
#   + 2  match in `verbanden.{laag1_refs, related, ...}`
#   + 1  match in `footnote.{bron, ...}`
#
# Ws5-gap awareness: elke kaart in het resultaat bevat `_ws5_gap: bool` zodat
# response_composer.py Spark kan laten melden "hé, ws5 leeg — help me even".
# ---------------------------------------------------------------------------

import re as _re
import unicodedata as _ud

# Nederlandse stopwoorden (kort — filtert veel-ruis maar houdt semantische kern)
_STOPWORDS = {
    "de", "het", "een", "en", "of", "maar", "als", "dan", "dus", "want",
    "die", "dat", "deze", "dit", "wat", "wie", "waar", "hoe", "wanneer", "waarom",
    "is", "was", "zijn", "waren", "wordt", "worden", "heeft", "hebben", "had",
    "ik", "jij", "je", "hij", "zij", "we", "wij", "jullie", "ze", "u", "me", "mij",
    "van", "voor", "met", "op", "in", "aan", "bij", "om", "over", "onder",
    "naar", "uit", "door", "tot", "tegen", "tussen", "na", "vóór", "voor",
    "niet", "geen", "wel", "ook", "nog", "al", "maar", "toch", "eens",
    "kan", "kunnen", "moet", "moeten", "wil", "willen", "zou", "zouden",
}


def _normalize(text) -> str:
    """Lowercase + strip accenten + collapse whitespace. Robuust voor None/int."""
    if text is None:
        return ""
    s = str(text).lower()
    s = _ud.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = _re.sub(r"[^a-z0-9\s]", " ", s)
    s = _re.sub(r"\s+", " ", s).strip()
    return s


def _tokenize(text) -> List[str]:
    """Splits + strip stopwoorden + minlen 2."""
    norm = _normalize(text)
    return [t for t in norm.split(" ") if t and len(t) >= 2 and t not in _STOPWORDS]


def _has_ws5_gap(card: Dict) -> bool:
    """True als >= 1 van de 5 W's leeg is."""
    ws5 = card.get("ws5") or {}
    for k in ("wie", "wat", "waar", "wanneer", "waarom"):
        v = ws5.get(k)
        if not v or not str(v).strip():
            return True
    return False


def _score_card(card: Dict, query_tokens: List[str]) -> Dict:
    """Score een kaart tegen query tokens. Return {score, matched_fields}."""
    if not query_tokens:
        return {"score": 0, "matched_fields": []}

    matched_fields: List[str] = []
    score = 0

    # 1. begrip (+10 per matching token, max 3× = +30)
    begrip_tokens = set(_tokenize(card.get("begrip")))
    begrip_hits = len(begrip_tokens & set(query_tokens))
    if begrip_hits:
        score += min(begrip_hits, 3) * 10
        matched_fields.append("begrip")

    # 2. ws5 waarden (+5 per matching token, max 5× = +25)
    ws5 = card.get("ws5") or {}
    ws5_text = " ".join(str(ws5.get(k, "")) for k in ("wie", "wat", "waar", "wanneer", "waarom"))
    ws5_tokens = set(_tokenize(ws5_text))
    ws5_hits = len(ws5_tokens & set(query_tokens))
    if ws5_hits:
        score += min(ws5_hits, 5) * 5
        matched_fields.append("ws5")

    # 3. tags (+3 per matching tag, max 5× = +15)
    tags = card.get("tags") or []
    tag_tokens = set()
    for t in tags:
        tag_tokens |= set(_tokenize(t))
    tag_hits = len(tag_tokens & set(query_tokens))
    if tag_hits:
        score += min(tag_hits, 5) * 3
        matched_fields.append("tags")

    # 4. verbanden (+2 per match; kan een lijst refs of dict zijn)
    verbanden = card.get("verbanden") or {}
    if isinstance(verbanden, dict):
        v_items: List = []
        for key in ("laag1_refs", "related", "gerelateerd", "referenties"):
            vv = verbanden.get(key)
            if isinstance(vv, list):
                v_items.extend(vv)
        v_text = " ".join(str(x) for x in v_items)
    else:
        v_text = str(verbanden)
    v_tokens = set(_tokenize(v_text))
    v_hits = len(v_tokens & set(query_tokens))
    if v_hits:
        score += min(v_hits, 5) * 2
        matched_fields.append("verbanden")

    # 5. footnote (+1 per match, alleen op tekstuele velden)
    footnote = card.get("footnote") or {}
    if isinstance(footnote, dict):
        fn_text = " ".join(str(v) for k, v in footnote.items()
                           if k in ("bron", "context", "notitie") and v)
    else:
        fn_text = str(footnote)
    fn_tokens = set(_tokenize(fn_text))
    fn_hits = len(fn_tokens & set(query_tokens))
    if fn_hits:
        score += min(fn_hits, 3) * 1
        matched_fields.append("footnote")

    # 6. lagen.laag1 (extra: soms de betekenis-tekst; +2 per match, max +6)
    lagen = card.get("lagen") or {}
    laag1_tokens = set(_tokenize(lagen.get("laag1")))
    l1_hits = len(laag1_tokens & set(query_tokens))
    if l1_hits:
        score += min(l1_hits, 3) * 2
        matched_fields.append("laag1")

    return {"score": score, "matched_fields": matched_fields}


def _all_cards_with_lade() -> List[Dict]:
    """Laad alle kaarten uit 4 lades + inbox, met `_lade` en `_source` velden."""
    all_cards: List[Dict] = []
    for lade in LADES:
        d = load_json(_lade_path(lade), default={"kaarten": []})
        for k in d.get("kaarten", []):
            k = dict(k)
            k["_lade"] = lade
            all_cards.append(k)
    inbox = load_json(_inbox_path(), default={"kaarten": []})
    for k in inbox.get("kaarten", []):
        k = dict(k)
        k["_lade"] = "inbox"
        all_cards.append(k)
    return all_cards


@traced(intent="Spark raadpleegt zijn eigen KB v2 kaarten op basis van user-vraag")
def semantic_lookup(query: str, top_n: int = 5, min_score: int = 5) -> Dict:
    """Zoek in alle KB v2 kaarten (begrip + tags + ws5 + verbanden + footnote + laag1).

    Args:
        query: user-vraag of trefwoord (Nederlands, vrije tekst)
        top_n: maximaal aantal kaarten terug (default 5)
        min_score: minimale score-drempel om terug te geven (filter ruis)

    Returns:
        {
          "query": str,
          "query_tokens": [str],
          "n_scanned": int,
          "n_matched": int,
          "results": [
            {
              "kaart": {...volledige kaart...},
              "score": int,
              "matched_fields": [str],
              "ws5_gap": bool,          # True als 1+ van 5 W's leeg
              "lade": str,              # voelen/spreken/weten/doen/inbox
            }
          ],
        }

    Voor response_composer.py: elke result bevat `ws5_gap`. Als True, kan Spark
    de gebruiker vragen om hulp: "ik vond 'X' relevant maar mijn W's zijn hier
    niet volledig. Wil je 'wie/wat/...' aanvullen?"
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return {"query": query, "query_tokens": [], "n_scanned": 0, "n_matched": 0, "results": []}

    all_cards = _all_cards_with_lade()
    all_cards = filter_fictie(all_cards, query)
    scored: List[Dict] = []
    for c in all_cards:
        s = _score_card(c, query_tokens)
        if s["score"] >= min_score:
            scored.append({
                "kaart": c,
                "score": s["score"],
                "matched_fields": s["matched_fields"],
                "ws5_gap": _has_ws5_gap(c),
                "lade": c.get("_lade", "?"),
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return {
        "query": query,
        "query_tokens": query_tokens,
        "n_scanned": len(all_cards),
        "n_matched": len(scored),
        "results": scored[:top_n],
    }


def list_lade(lade: str, limit: int = 50, offset: int = 0, search: str = "") -> Dict:
    """Lijst kaarten in 1 lade. Paged + optioneel zoekfilter op 'begrip'."""
    if lade not in LADES:
        return {"error": f"Onbekende lade '{lade}'"}
    data = load_json(_lade_path(lade), default={"kaarten": []})
    kaarten = data.get("kaarten", [])
    if search:
        s = search.lower().strip()
        kaarten = [k for k in kaarten if s in (k.get("begrip", "") or "").lower()]
    total = len(kaarten)
    # v6_kbv2_sort_recent — recent ingedeeld/bewerkt eerst (in plaats van alfabetisch)
    def _ts(k):
        fn = k.get("footnote") or {}
        return fn.get("laatst_bewerkt_op") or fn.get("ingedeeld_op") or fn.get("aangemaakt_op") or ""
    kaarten = sorted(kaarten, key=lambda k: (k.get("begrip") or "").lower())
    kaarten = sorted(kaarten, key=_ts, reverse=True)
    return {
        "lade": lade,
        **LADE_META[lade],
        "total": total,
        "offset": offset,
        "limit": limit,
        "kaarten": kaarten[offset:offset + limit],
    }


def list_inbox(limit: int = 50, offset: int = 0, reason: str = "", search: str = "",
               sort: str = "recent") -> Dict:
    """Lijst onbeantwoorde kaarten met optionele filter op _inbox_reason.

    v12_kbv2_inbox_sort_001 — sort opties:
      - 'recent' (default): nieuwste bewerkt/toegevoegd eerst
      - 'oud': oudste eerst
      - 'alfa': alfabetisch A-Z
      - 'alfa_desc': alfabetisch Z-A
      - 'hits_desc': meeste 'hits' eerst (laag1_refs uit andere kaarten — Top 50 prio-modus)
      - 'hits_asc': minste hits eerst
    """
    data = load_json(_inbox_path(), default={"kaarten": []})
    kaarten = data.get("kaarten", [])

    # v13_kbv2_inbox_dedupe_002 — Filter LEGE inbox-kaarten weg als het begrip
    # elders in een lade al mét gevulde laag1 bestaat. Data zelf blijft intact
    # (admin /dedupe-inbox verwijdert pas permanent), dit is de read-side guard
    # zodat Willem geen dubbele kaarten meer ziet in Kennisbank → Inbox.
    _lade_filled = _begrippen_filled_in_lades()
    if _lade_filled:
        _pre = len(kaarten)
        _filtered = []
        for k in kaarten:
            b = (k.get("begrip") or "").lower().strip()
            l1 = ((k.get("lagen", {}) or {}).get("laag1", "") if isinstance(k.get("lagen"), dict) else "") or ""
            # skip: leeg inbox-kaart maar begrip staat al gevuld in een lade
            if b and b in _lade_filled and not l1.strip():
                continue
            _filtered.append(k)
        kaarten = _filtered
        # transparant meesturen naar UI zodat we weten hoeveel we geskipt hebben
        _hidden_dupes = _pre - len(kaarten)
    else:
        _hidden_dupes = 0

    if reason:
        kaarten = [k for k in kaarten if k.get("_inbox_reason") == reason]
    if search:
        s = search.lower().strip()
        kaarten = [k for k in kaarten if s in (k.get("begrip", "") or "").lower()]
    total = len(kaarten)

    def _ts(k):
        fn = k.get("footnote") or {}
        return fn.get("aangemaakt_op") or fn.get("laatst_bewerkt_op") or ""

    if sort == "alfa":
        kaarten = sorted(kaarten, key=lambda k: (k.get("begrip") or "").lower())
    elif sort == "alfa_desc":
        kaarten = sorted(kaarten, key=lambda k: (k.get("begrip") or "").lower(), reverse=True)
    elif sort == "oud":
        kaarten = sorted(kaarten, key=_ts)  # oude eerst
    elif sort in ("hits_desc", "hits_asc"):
        # Gebruik laag1_refs (hoeveel andere kaarten dit woord in laag1 noemen)
        signals = _build_priority_signals()
        laag1_refs = signals.get("laag1_refs", {})
        kaarten = sorted(
            kaarten,
            key=lambda k: laag1_refs.get((k.get("begrip") or "").lower(), 0),
            reverse=(sort == "hits_desc"),
        )
    else:  # 'recent' (default) — huidige gedrag: alfabetisch → reden-prio → ts desc
        priority = {"tag_tie": 1, "no_match": 2, "missing_laag1": 3}
        kaarten = sorted(kaarten, key=lambda k: (k.get("begrip") or "").lower())
        kaarten = sorted(kaarten, key=lambda k: priority.get(k.get("_inbox_reason", ""), 9))
        kaarten = sorted(kaarten, key=_ts, reverse=True)

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "sort": sort,
        "kaarten": kaarten[offset:offset + limit],
        "redenen": _count_reasons(data.get("kaarten", [])),
        "hidden_dupes_in_lade": _hidden_dupes,
    }


def _build_priority_signals() -> Dict:
    """v6_kbv2_priority_002 — Bouw de externe signaal-indexes voor prio-scoring.
    Wordt 1× per priority-call gebouwd, niet per kaart (anders O(n²)).

    Returns dict met:
      vocab_active: set van begrip.lower() die in spark_vocab.active=True staan
      intent_freq: dict begrip.lower() → aantal keer dat woord in laatste 500 intents voorkomt
      laag1_refs:  dict begrip.lower() → aantal andere lade-kaarten die dit woord in laag1 noemen
    """
    # NL stopwoorden — filter uit cross-ref/intent zodat "zijn, niet, manier" niet bovenaan komen
    STOP = {
        "een", "het", "die", "deze", "dit", "dat", "der", "den", "des", "wie", "wat",
        "waar", "wanneer", "hoe", "waarom", "alle", "alles", "iets", "niets", "zo", "ook",
        "maar", "want", "omdat", "dus", "toch", "echter", "want", "of", "en", "noch",
        "niet", "wel", "geen", "naar", "over", "voor", "uit", "door", "tegen", "tussen",
        "achter", "boven", "onder", "binnen", "buiten", "tijdens", "zonder", "vanaf",
        "vooral", "alleen", "even", "alvast", "graag", "ergens", "overal", "nergens",
        "hier", "daar", "ginds", "vandaag", "morgen", "gisteren", "nu", "later", "altijd",
        "soms", "vaak", "nooit", "meestal", "weer", "opnieuw", "snel", "langzaam",
        "zijn", "ben", "bent", "was", "waren", "geweest", "worden", "wordt", "werd",
        "heeft", "hebben", "had", "hadden", "gehad", "doen", "doet", "deed", "gedaan",
        "gaat", "gaan", "ging", "gingen", "gegaan", "komen", "komt", "kwam", "kwamen",
        "gekomen", "kan", "kun", "kunnen", "kon", "konden", "moet", "moeten", "moest",
        "moesten", "mag", "mogen", "mocht", "mochten", "wil", "willen", "wilde",
        "wilden", "zal", "zou", "zouden", "ja", "nee", "misschien", "vast", "wel",
        "zelf", "alleen", "samen", "ergens", "geven", "geeft", "gaf", "gegeven",
        "maken", "maakt", "maakte", "gemaakt", "zien", "zie", "zag", "gezien",
        "laten", "laat", "liet", "gelaten", "vinden", "vindt", "vond", "gevonden",
        "weten", "weet", "wist", "geweten", "zeggen", "zegt", "zei", "gezegd",
        "manier", "deel", "kant", "ding", "dingen", "klein", "groot", "veel", "weinig",
        "meer", "minder", "iets", "twee", "drie", "vier", "vijf", "kenmerken",
        "uitspraak", "andere", "anders", "elke", "elk", "iedere", "alle", "alles",
        "mij", "jou", "hem", "haar", "ons", "jullie", "hen", "hun", "ze", "we", "je",
    }

    base = Path(__file__).parent.parent.parent / "data"
    # 1. Vocab actives
    vocab_active = set()
    try:
        vdata = load_json(base / "personality" / "spark_vocab.json", default={"vocab": {}})
        for word, entry in vdata.get("vocab", {}).items():
            if isinstance(entry, dict) and entry.get("active"):
                vocab_active.add(word.lower())
    except Exception:
        pass

    def _is_signal_word(w: str) -> bool:
        return len(w) >= 4 and w not in STOP

    # 2. Intent frequencies (laatste 500 regels)
    intent_freq: Dict[str, int] = {}
    intent_log = base / "system" / "intent_log.jsonl"
    try:
        if intent_log.exists():
            import json as _json
            with open(intent_log, "r") as f:
                lines = f.readlines()[-500:]
            for line in lines:
                try:
                    obj = _json.loads(line)
                    text = (obj.get("text") or "").lower()
                    for w in text.replace(".", " ").replace(",", " ").replace("?", " ").split():
                        if _is_signal_word(w):
                            intent_freq[w] = intent_freq.get(w, 0) + 1
                except Exception:
                    continue
    except Exception:
        pass

    # 3. Cross-references in laag1 van andere lade-kaarten
    laag1_refs: Dict[str, int] = {}
    for lade in LADES:
        try:
            ldata = load_json(V2_DIR / f"knowledge_v2_{lade}.json", default={"kaarten": []})
            for k in ldata.get("kaarten", []):
                laag1 = ((k.get("lagen") or {}).get("laag1") or "").lower()
                if not laag1:
                    continue
                for w in laag1.replace(".", " ").replace(",", " ").split():
                    if _is_signal_word(w):
                        laag1_refs[w] = laag1_refs.get(w, 0) + 1
        except Exception:
            continue

    return {
        "vocab_active": vocab_active,
        "intent_freq": intent_freq,
        "laag1_refs": laag1_refs,
    }


def list_priority_missing_laag1(limit: int = 50, reverse: bool = False) -> Dict:
    """
    v6_kbv2_priority_002 — Top N kaarten zonder laag1, gesorteerd op echte signalen
    i.p.v. alleen interne tags/verbanden.

    Score-formule (hoger = belangrijker om eerst in te vullen):
      + 10 punten als Spark dit woord al active gebruikt (spark_vocab.active=true)
                    → kaart "vult zichzelf in" als context voor Spark's eigen taal
      +  5 punten per keer dat het woord in de laag1 van andere lade-kaarten staat
                    → cross-reference: woord is fundament voor andere kennis
      +  3 punten per keer dat het woord in laatste 500 intents is getypt
                    → mensen vragen Spark al over dit begrip
      +  3 punten per bestaand verband (kaart wordt al ergens aan gerefereerd)
      +  5 punten als topic gevuld is (Spark heeft 5W-vragen er over gehad)
      +  2 punten als ws5 gedeeltelijk gevuld is
      +  1 punt per tag (mild signaal)

    Returnt: kaarten[] met {id, begrip, lade, score, reasons[], breakdown}
    """
    data = load_json(_inbox_path(), default={"kaarten": []})
    kaarten = data.get("kaarten", [])
    no_laag1 = [k for k in kaarten if not (k.get("lagen") or {}).get("laag1", "").strip()]

    sig = _build_priority_signals()
    vocab_active = sig["vocab_active"]
    intent_freq = sig["intent_freq"]
    laag1_refs = sig["laag1_refs"]

    scored = []
    for k in no_laag1:
        score = 0
        reasons = []
        breakdown: Dict[str, int] = {}
        begrip = (k.get("begrip") or "").strip().lower()

        # NIEUW: 1. Vocab-active boost
        if begrip and begrip in vocab_active:
            score += 10
            reasons.append("Spark gebruikt dit al active (+10)")
            breakdown["vocab_active"] = 10

        # NIEUW: 2. Cross-reference in laag1
        if begrip and begrip in laag1_refs:
            n = laag1_refs[begrip]
            pts = n * 5
            score += pts
            reasons.append(f"{n}× genoemd in andere kaarten laag1 (×5)")
            breakdown["laag1_refs"] = pts

        # NIEUW: 3. Intent frequency
        if begrip and begrip in intent_freq:
            n = intent_freq[begrip]
            pts = n * 3
            score += pts
            reasons.append(f"{n}× getypt in recente intents (×3)")
            breakdown["intent_freq"] = pts

        # Bestaande signalen
        verbanden = k.get("verbanden") or []
        if verbanden:
            n = len(verbanden)
            pts = n * 3
            score += pts
            reasons.append(f"{n} verbanden (×3)")
            breakdown["verbanden"] = pts

        tags = k.get("tags") or []
        if isinstance(tags, list):
            n_tags = sum(len(str(t).split(",")) for t in tags) if tags and isinstance(tags[0], str) and "," in str(tags[0]) else len(tags)
        else:
            n_tags = 0
        if n_tags:
            score += n_tags
            reasons.append(f"{n_tags} tags (×1)")
            breakdown["tags"] = n_tags

        topic = (k.get("topic") or "").strip()
        if topic:
            score += 5
            reasons.append("topic gevuld (+5)")
            breakdown["topic"] = 5
        ws5 = k.get("ws5") or {}
        if isinstance(ws5, dict) and any(v for v in ws5.values() if v):
            score += 2
            reasons.append("ws5 gedeeltelijk (+2)")
            breakdown["ws5"] = 2

        scored.append({
            "id": k.get("id"),
            "begrip": k.get("begrip"),
            "lade": k.get("lade"),
            "_inbox_reason": k.get("_inbox_reason"),
            "tags_count": n_tags,
            "verbanden_count": len(verbanden),
            "has_topic": bool(topic),
            "has_ws5_partial": isinstance(ws5, dict) and any(v for v in ws5.values() if v),
            "vocab_active": begrip in vocab_active,
            "laag1_refs": laag1_refs.get(begrip, 0),
            "intent_freq": intent_freq.get(begrip, 0),
            "score": score,
            "reasons": reasons,
            "breakdown": breakdown,
        })

    # v12_kbv2_inbox_sort_001 — reverse=True → 'minste hits eerst' (score oplopend)
    scored.sort(key=lambda x: x["score"], reverse=not reverse)
    return {
        "total_missing_laag1": len(no_laag1),
        "limit": limit,
        "formula_version": "v2",
        "signals_used": {
            "vocab_active_count": len(vocab_active),
            "intent_words_indexed": len(intent_freq),
            "laag1_refs_indexed": len(laag1_refs),
        },
        "kaarten": scored[:limit],
    }


def _count_reasons(cards: List[Dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for c in cards:
        r = c.get("_inbox_reason") or "onbekend"
        out[r] = out.get(r, 0) + 1
    return out


def find_by_begrip(begrip: str) -> Optional[Dict]:
    """Snelle lookup via index. Returnt kaart + lade-info of None."""
    idx = load_json(_index_path(), default={"entries": {}})
    entries = idx.get("entries", {})
    e = entries.get(begrip.lower().strip())
    if not e:
        return None
    lade = e.get("lade")
    kaart_id = e.get("kaart_id")
    if lade:
        bucket = load_json(_lade_path(lade), default={"kaarten": []})
    else:
        bucket = load_json(_inbox_path(), default={"kaarten": []})
    for k in bucket.get("kaarten", []):
        if k.get("id") == kaart_id:
            return {"kaart": k, "lade": lade, "found_in": "lade" if lade else "inbox"}
    return None


def audit() -> Dict:
    """Self-audit: scan v2 op kaarten met lege lagen, ontbrekende footnote, etc.
    Geïnspireerd op v1's AuditService — pure heuristic, geen AI."""
    findings = {
        "empty_laag1": [],
        "missing_footnote": [],
        "low_confidence": [],
        "no_tags": [],
        "inbox_ties": 0,
        "inbox_no_match": 0,
        "inbox_missing_laag1": 0,
    }
    for lade in LADES:
        d = load_json(_lade_path(lade), default={"kaarten": []})
        for k in d.get("kaarten", []):
            lagen = k.get("lagen") or {}
            if not (lagen.get("laag1") or "").strip():
                findings["empty_laag1"].append({"id": k["id"], "begrip": k["begrip"], "lade": lade})
            if not k.get("footnote"):
                findings["missing_footnote"].append({"id": k["id"], "begrip": k["begrip"], "lade": lade})
            elif (k.get("footnote", {}).get("vertrouwen") or 0) < 0.5:
                findings["low_confidence"].append({"id": k["id"], "begrip": k["begrip"], "lade": lade,
                                                    "vertrouwen": k["footnote"]["vertrouwen"]})
            if not k.get("tags"):
                findings["no_tags"].append({"id": k["id"], "begrip": k["begrip"], "lade": lade})

    inbox = load_json(_inbox_path(), default={"kaarten": []})
    for k in inbox.get("kaarten", []):
        r = k.get("_inbox_reason")
        if r == "tag_tie":
            findings["inbox_ties"] += 1
        elif r == "no_match":
            findings["inbox_no_match"] += 1
        elif r == "missing_laag1":
            findings["inbox_missing_laag1"] += 1

    summary = {
        "empty_laag1_count": len(findings["empty_laag1"]),
        "missing_footnote_count": len(findings["missing_footnote"]),
        "low_confidence_count": len(findings["low_confidence"]),
        "no_tags_count": len(findings["no_tags"]),
        "inbox_ties": findings["inbox_ties"],
        "inbox_no_match": findings["inbox_no_match"],
        "inbox_missing_laag1": findings["inbox_missing_laag1"],
    }
    log_event("kbv2", "audit", intent="self-audit kb v2", detail=summary)
    # Beperk findings-lijsten tot top 50 voor UI
    for k in ("empty_laag1", "missing_footnote", "low_confidence", "no_tags"):
        findings[k] = findings[k][:50]
    return {"summary": summary, "findings": findings, "audited_at": _now()}


# ---------------------------------------------------------------------------
# Write API
# ---------------------------------------------------------------------------

@traced(intent="kaart uit inbox in lade plaatsen", module="kbv2")
def classify_card(card_id: str, lade: str, updates: Optional[Dict] = None,
                  user_id: str = "user-000") -> Dict:
    """Verplaats kaart van Inbox naar gekozen lade. Optioneel met edits aan lagen/ws5.
    Werkt index bij. Idempotent als kaart al in lade staat.
    """
    if lade not in LADES:
        return {"success": False, "message": f"Onbekende lade '{lade}'"}

    with _lock:
        inbox = load_json(_inbox_path(), default={"kaarten": []})
        lade_data = load_json(_lade_path(lade), default={"kaarten": []})
        idx = load_json(_index_path(), default={"entries": {}})

        # Vind kaart in inbox
        target_idx = None
        for i, k in enumerate(inbox.get("kaarten", [])):
            if k.get("id") == card_id:
                target_idx = i
                break
        if target_idx is None:
            # Misschien staat hij al in een lade?
            for L in LADES:
                ld = load_json(_lade_path(L), default={"kaarten": []})
                for k in ld.get("kaarten", []):
                    if k.get("id") == card_id:
                        return {"success": False, "message": f"Kaart staat al in lade '{L}'"}
            return {"success": False, "message": f"Kaart '{card_id}' niet gevonden"}

        # v14_min_tags_001 — geen lade zonder ≥5 tags
        _gate_tags = (updates.get("tags") if updates and updates.get("tags") is not None else inbox["kaarten"][target_idx].get("tags"))
        _gate_msg = tags_gate(_gate_tags)
        if _gate_msg:
            return {"success": False, "message": _gate_msg, "reason": "min_tags", "tags_count": len(_gate_tags or []), "min_tags": MIN_TAGS_FOR_LADE}

        card = inbox["kaarten"].pop(target_idx)
        card["lade"] = lade

        # v10_kbv2_classify_dupe_guard_002 — Homoniem-aware dupe-check (Willems note sessie 47).
        # Zelfde begrip in doel-lade is alleen echte dupe als tag-sets OVERLAPPEN.
        # Bij lege intersect + beide kaarten ≥1 tag → homoniem (bv. `banken` = financieel én meubel),
        # allebei toestaan. Bij tag-overlap of één zonder tags → weiger (echte dupe).
        _nb = (card.get("begrip") or "").lower().strip()
        _new_tags = {t.lower().strip() for t in (updates.get("tags") if updates else None) or card.get("tags") or [] if t}
        _existing_in_lade = None
        for _k in (lade_data.get("kaarten") or []):
            if (_k.get("begrip") or "").lower().strip() != _nb:
                continue
            _ex_tags = {t.lower().strip() for t in (_k.get("tags") or []) if t}
            _has_overlap = bool(_new_tags & _ex_tags)
            _both_have_tags = bool(_new_tags) and bool(_ex_tags)
            # ECHTE dupe: tag-overlap OF één van beide heeft geen tags
            if _has_overlap or not _both_have_tags:
                _existing_in_lade = _k
                break
            # Anders: disjunkte tags op beide → homoniem, sta toe (loop verder)
        if _existing_in_lade:
            inbox["kaarten"].insert(target_idx, card)  # rollback
            return {
                "success": False,
                "message": (
                    f"Begrip '{card.get('begrip')}' bestaat al in lade '{lade}' (id={_existing_in_lade.get('id')}). "
                    "Merge handmatig, kies andere lade, of geef beide kaarten unieke tags om als homoniem te scheiden."
                ),
                "duplicate_in_lade": lade,
                "existing_card_id": _existing_in_lade.get("id"),
                "existing_card_begrip": _existing_in_lade.get("begrip"),
                "existing_card_tags": _existing_in_lade.get("tags") or [],
                "new_card_tags": list(_new_tags),
                "hint": "tag-based homoniem-guard: tags moeten NIET overlappen én beide moeten ≥1 tag hebben.",
            }

        # Verwijder migratie-meta
        card.pop("_inbox_reason", None)
        card.pop("_classifier_scores", None)
        # Apply updates aan lagen / ws5 / tags
        if updates:
            if "lagen" in updates:
                card["lagen"] = {**(card.get("lagen") or {}), **(updates["lagen"] or {})}
            if "ws5" in updates:
                card["ws5"] = {**(card.get("ws5") or {}), **(updates["ws5"] or {})}
            if "tags" in updates and isinstance(updates["tags"], list):
                card["tags"] = updates["tags"]
        # Footnote-update
        fn = card.get("footnote") or {}
        fn["ingedeeld_door"] = user_id
        fn["ingedeeld_op"] = _now()
        # Recompute confidence based on filled lagen
        lagen_filled = sum(1 for v in (card.get("lagen") or {}).values() if (v or "").strip())
        fn["vertrouwen"] = max(fn.get("vertrouwen", 0.5), round(0.5 + 0.1 * lagen_filled, 2))
        card["footnote"] = fn
        # v5_kbv2_media_001 — needs-checklist bijwerken
        card.setdefault("media", {"voice_url": None, "voice_transcript": None, "image_urls": []})
        card["needs"] = _compute_needs(card)

        # Schrijf weg
        lade_data.setdefault("kaarten", []).append(card)
        lade_data["metadata"] = lade_data.get("metadata") or {}
        lade_data["metadata"]["card_count"] = len(lade_data["kaarten"])
        lade_data["metadata"]["last_updated"] = _now()

        save_json(_lade_path(lade), lade_data)
        save_json(_inbox_path(), inbox)

        # Index update
        idx.setdefault("entries", {})[(card.get("begrip") or "").lower().strip()] = {
            "kaart_id": card["id"],
            "lade": lade,
            "has_lagen": [k for k, v in (card.get("lagen") or {}).items() if v],
            "last_updated": _now(),
        }
        save_json(_index_path(), idx)

    # v6_kbv2_hooks_landing_001 — 5 hooks landen (post-save zodat data consistent is)
    _fire_post_classify_hooks(card, lade)

    return {"success": True, "kaart": card, "lade": lade}


def _fire_post_classify_hooks(card: Dict, lade: str) -> None:
    """v6_kbv2_hooks_landing_001 — fire hooks 1/3/4 na succesvolle classify/edit.
    Faalt graceful (try/except per hook) zodat 1 broken hook nooit een save blokkeert."""
    # v6_kbv2_unify_snap_001 — Invalidate snap-cache zodat chat direct
    # de nieuwe/bewerkte V2-kaart kan vinden (lookup-pad leest nu uit V2).
    try:
        from modules.chat.snap_service import SnapNLPService
        SnapNLPService().invalidate_cache()
    except Exception:
        pass
    try:
        from . import hooks as kbv2_hooks
    except Exception:
        return
    # Hook 1: Vocab register
    try:
        kbv2_hooks.register_in_vocab(card)
    except Exception as e:
        log_event("kbv2_hooks", "register_in_vocab_error", intent="hook-fail", detail={"err": str(e)[:120]})
    # Hook 3: Auto-graph verbanden
    try:
        verbanden = kbv2_hooks.compute_verbanden(card)
        if verbanden:
            # Schrijf terug in de kaart
            with _lock:
                if lade and lade != "inbox":
                    d = load_json(_lade_path(lade), default={"kaarten": []})
                    for k in d.get("kaarten", []):
                        if k.get("id") == card.get("id"):
                            k["verbanden"] = verbanden
                            # Sync footnote.hooks_fired uit in-memory card
                            if card.get("footnote", {}).get("hooks_fired"):
                                k.setdefault("footnote", {})["hooks_fired"] = card["footnote"]["hooks_fired"]
                            break
                    save_json(_lade_path(lade), d)
    except Exception as e:
        log_event("kbv2_hooks", "compute_verbanden_error", intent="hook-fail", detail={"err": str(e)[:120]})
    # Hook 4: D&D koppeling
    try:
        kbv2_hooks.link_to_dnd(card)
    except Exception as e:
        log_event("kbv2_hooks", "link_to_dnd_error", intent="hook-fail", detail={"err": str(e)[:120]})


EMOTIES = ("blij", "boos", "bang", "bedroefd", "neutraal")


def _apply_emotie(k: Dict, updates: Dict, user_id: str) -> None:
    """v14_emotie_veld_001 — bevestigde emotie zetten (neutraal is een echte keuze, geen default)."""
    e = updates.get("emotie")
    if isinstance(e, str) and e.lower().strip() in EMOTIES:
        k["emotie"] = e.lower().strip()
        k["emotie_bevestigd"] = True
        k["emotie_bron"] = user_id
        k["emotie_bevestigd_op"] = _now()


@traced(intent="bestaande kaart in lade bewerken", module="kbv2")
def edit_card(card_id: str, lade: str, updates: Dict, user_id: str = "user-000") -> Dict:
    """Update lagen / ws5 / tags / begrip van een kaart die al in een lade staat OF in inbox."""
    # v6_kbv2_edit_inbox_001 — laat inbox-kaarten ook bewerken (voor zelf-classify flow)
    if lade == "inbox":
        from pathlib import Path as _P
        inbox_path = _P(__file__).parent.parent.parent / "data" / "knowledge" / "v2" / "knowledge_inbox.json"
        with _lock:
            data = load_json(inbox_path, default={"kaarten": []})
            for k in data.get("kaarten", []):
                if k.get("id") == card_id:
                    if "lagen" in updates:
                        k["lagen"] = {**(k.get("lagen") or {}), **(updates["lagen"] or {})}
                    if "ws5" in updates:
                        k["ws5"] = {**(k.get("ws5") or {}), **(updates["ws5"] or {})}
                    if "tags" in updates and isinstance(updates["tags"], list):
                        k["tags"] = updates["tags"]
                    if "begrip" in updates and updates["begrip"]:
                        k["begrip"] = updates["begrip"]
                    if "media" in updates and isinstance(updates["media"], dict):
                        k["media"] = {**(k.get("media") or {}), **updates["media"]}
                    _apply_emotie(k, updates, user_id)
                    fn = k.get("footnote") or {}
                    fn["laatst_bewerkt_door"] = user_id
                    fn["laatst_bewerkt_op"] = _now()
                    k["footnote"] = fn
                    k.setdefault("media", {"voice_url": None, "voice_transcript": None, "image_urls": []})
                    k["needs"] = _compute_needs(k)
                    # v6_kbv2_unify_001 — wis _inbox_reason als laag1 nu gevuld is
                    if (k.get("lagen") or {}).get("laag1", "").strip():
                        if k.get("_inbox_reason") == "missing_laag1":
                            k.pop("_inbox_reason", None)
                    save_json(inbox_path, data)
                    # v6_kbv2_hooks_landing_001 — herfire hooks ook bij inbox-edit
                    _fire_post_classify_hooks(k, "inbox")
                    return {"success": True, "kaart": k}
            return {"success": False, "message": f"Inbox-kaart '{card_id}' niet gevonden"}
    if lade not in LADES:
        return {"success": False, "message": f"Onbekende lade '{lade}'"}
    with _lock:
        data = load_json(_lade_path(lade), default={"kaarten": []})
        for k in data.get("kaarten", []):
            if k.get("id") == card_id:
                if "lagen" in updates:
                    k["lagen"] = {**(k.get("lagen") or {}), **(updates["lagen"] or {})}
                if "ws5" in updates:
                    k["ws5"] = {**(k.get("ws5") or {}), **(updates["ws5"] or {})}
                if "tags" in updates and isinstance(updates["tags"], list):
                    k["tags"] = updates["tags"]
                if "begrip" in updates and updates["begrip"]:
                    k["begrip"] = updates["begrip"]
                # v5_kbv2_media_001 — media-updates (voice + images)
                if "media" in updates and isinstance(updates["media"], dict):
                    k["media"] = {**(k.get("media") or {}), **updates["media"]}
                _apply_emotie(k, updates, user_id)
                fn = k.get("footnote") or {}
                fn["laatst_bewerkt_door"] = user_id
                fn["laatst_bewerkt_op"] = _now()
                k["footnote"] = fn
                k.setdefault("media", {"voice_url": None, "voice_transcript": None, "image_urls": []})
                k["needs"] = _compute_needs(k)
                save_json(_lade_path(lade), data)
                # Index bijwerken
                idx = load_json(_index_path(), default={"entries": {}})
                idx.setdefault("entries", {})[k["begrip"].lower().strip()] = {
                    "kaart_id": k["id"], "lade": lade,
                    "has_lagen": [kk for kk, vv in k["lagen"].items() if vv],
                    "last_updated": _now(),
                }
                save_json(_index_path(), idx)
                # v6_kbv2_hooks_landing_001 — herfire hooks na elke edit (lade-kaart)
                _fire_post_classify_hooks(k, lade)
                return {"success": True, "kaart": k}
    return {"success": False, "message": f"Kaart '{card_id}' niet gevonden in lade '{lade}'"}


# v6_kbv2_move_card_001 — verplaats een kaart van de ene lade naar de andere
@traced(intent="kaart verplaatsen tussen lades", module="kbv2")
def move_card(card_id: str, from_lade: str, to_lade: str, user_id: str = "user-000") -> Dict:
    """Verplaats een kaart (incl. id, lagen, ws5, tags, media, footnote) van
    `from_lade` naar `to_lade`. Werkt voor alle combinaties van weten/doen/voelen/spreken/inbox.
    """
    def _path_for(lade_name):
        return _inbox_path() if lade_name == "inbox" else _lade_path(lade_name)

    if from_lade == to_lade:
        return {"success": False, "message": "Bron- en doel-lade zijn gelijk"}
    if from_lade not in LADES and from_lade != "inbox":
        return {"success": False, "message": f"Onbekende from_lade '{from_lade}'"}
    if to_lade not in LADES and to_lade != "inbox":
        return {"success": False, "message": f"Onbekende to_lade '{to_lade}'"}

    src_path = _path_for(from_lade)
    dst_path = _path_for(to_lade)
    with _lock:
        src_data = load_json(src_path, default={"kaarten": []})
        dst_data = load_json(dst_path, default={"kaarten": []})
        kaarten = src_data.get("kaarten", [])
        idx = next((i for i, k in enumerate(kaarten) if k.get("id") == card_id), -1)
        if idx < 0:
            return {"success": False, "message": f"Kaart '{card_id}' niet in lade '{from_lade}'"}
        card = kaarten[idx]

        # v10_kbv2_move_dupe_guard_001 — Homoniem-aware guard bij verplaatsen.
        # Zelfde begrip in doel-lade = echte dupe TENZIJ beide kaarten disjunkte tags hebben (≥1 elk).
        _nb = (card.get("begrip") or "").lower().strip()
        _new_tags = {t.lower().strip() for t in (card.get("tags") or []) if t}
        for _dk in (dst_data.get("kaarten") or []):
            if (_dk.get("begrip") or "").lower().strip() != _nb:
                continue
            _ex_tags = {t.lower().strip() for t in (_dk.get("tags") or []) if t}
            _has_overlap = bool(_new_tags & _ex_tags)
            _both_have_tags = bool(_new_tags) and bool(_ex_tags)
            if _has_overlap or not _both_have_tags:
                return {
                    "success": False,
                    "message": (
                        f"Begrip '{card.get('begrip')}' bestaat al in '{to_lade}' (id={_dk.get('id')}). "
                        "Geef beide kaarten unieke tags voor homoniem-scheiding."
                    ),
                    "duplicate_in_lade": to_lade,
                    "existing_card_id": _dk.get("id"),
                    "existing_card_tags": _dk.get("tags") or [],
                    "new_card_tags": list(_new_tags),
                }
            # Anders: disjunkte tags op beide → homoniem, sta toe

        card = kaarten.pop(idx)
        card["lade"] = to_lade
        fn = card.get("footnote") or {}
        fn["laatst_bewerkt_door"] = user_id
        fn["laatst_bewerkt_op"] = _now()
        fn.setdefault("moves", []).append({
            "from": from_lade, "to": to_lade, "by": user_id, "op": _now(),
        })
        card["footnote"] = fn
        # Voorkom duplicaat op doel
        dst_data.setdefault("kaarten", [])
        if not any(k.get("id") == card_id for k in dst_data["kaarten"]):
            dst_data["kaarten"].append(card)
        src_data["kaarten"] = kaarten
        save_json(src_path, src_data)
        save_json(dst_path, dst_data)
        # Update index
        idx_data = load_json(_index_path(), default={"entries": {}})
        idx_data.setdefault("entries", {})[(card.get("begrip") or "").lower().strip()] = {
            "kaart_id": card_id, "lade": to_lade,
            "has_lagen": [kk for kk, vv in (card.get("lagen") or {}).items() if vv],
            "last_updated": _now(),
        }
        save_json(_index_path(), idx_data)
    return {"success": True, "kaart": card, "from": from_lade, "to": to_lade}


@traced(intent="nieuwe kaart toevoegen aan inbox", module="kbv2")
def add_to_inbox(begrip: str, source: str = "user", user_id: str = "user-000", deep_scan: bool = False) -> Dict:
    """Maak een lege kaart in de inbox (bv. wanneer Spark een onbekend woord tegenkomt).
    Idempotent: als 'begrip' al ergens bestaat, return existing.

    v7_kbv2_add_perf_001 — deep_scan default FALSE. Voorheen: bij elke add scanden
    we alle 4 lade-files (~16MB) + inbox (~2MB) → 18MB IO per POST → langzaam →
    user klikte opnieuw → race condition. Nu: vertrouw index (snel).
    Gebruik `deep_scan=True` alleen als je index-corruptie vermoedt.
    """
    if not begrip or not begrip.strip():
        return {"success": False, "message": "Leeg begrip"}
    nb = begrip.lower().strip()

    # 1. Snelle index-check
    existing = find_by_begrip(begrip)
    if existing:
        return {"success": True, "kaart": existing["kaart"], "existing": True, "lade": existing["lade"]}

    # 1b. v13_kbv2_inbox_dedupe_002 — Index-miss fallback:
    # Index kan stale zijn (herbouwd, backup restore, race). Voordat we een
    # nieuwe (mogelijk dubbele) kaart aanmaken, doen we ALTIJD een deep-scan
    # over de 4 lade-bestanden. Als het begrip daar al gevuld staat: return
    # existing + auto-repair index. Dit voorkomt de "dubbele kaart" bug.
    _lade_hit = _begrippen_filled_in_lades().get(nb)
    if _lade_hit:
        _lade_name, _lade_id = _lade_hit
        ld = load_json(_lade_path(_lade_name), default={"kaarten": []})
        _kaart = next((k for k in ld.get("kaarten", []) if k.get("id") == _lade_id), None)
        if _kaart:
            # herstel index
            idx = load_json(_index_path(), default={"entries": {}})
            idx.setdefault("entries", {})[nb] = {
                "kaart_id": _lade_id, "lade": _lade_name,
                "has_lagen": [k for k, v in (_kaart.get("lagen") or {}).items() if (v or "").strip()],
                "last_updated": _now(),
            }
            save_json(_index_path(), idx)
            return {
                "success": True, "kaart": _kaart, "existing": True,
                "lade": _lade_name, "repaired_index": True,
                "skipped_reason": "already_filled_in_lade",
            }

    # 2. Deep scan alleen expliciet aanvragen (was default → grote IO-kosten)
    if deep_scan:
        for L in LADES:
            ld = load_json(_lade_path(L), default={"kaarten": []})
            for k in ld.get("kaarten", []):
                if (k.get("begrip") or "").lower().strip() == nb:
                    idx = load_json(_index_path(), default={"entries": {}})
                    idx.setdefault("entries", {})[nb] = {
                        "kaart_id": k.get("id"), "lade": L,
                        "has_lagen": [kk for kk, vv in (k.get("lagen") or {}).items() if vv],
                        "last_updated": _now(),
                    }
                    save_json(_index_path(), idx)
                    return {"success": True, "kaart": k, "existing": True, "lade": L,
                            "repaired_index": True}
        inbox_check = load_json(_inbox_path(), default={"kaarten": []})
        for k in inbox_check.get("kaarten", []):
            if (k.get("begrip") or "").lower().strip() == nb:
                idx = load_json(_index_path(), default={"entries": {}})
                idx.setdefault("entries", {})[nb] = {
                    "kaart_id": k.get("id"), "lade": None,
                    "has_lagen": [], "last_updated": _now(),
                }
                save_json(_index_path(), idx)
                return {"success": True, "kaart": k, "existing": True, "lade": None,
                        "repaired_index": True}

    with _lock:
        inbox = load_json(_inbox_path(), default={"kaarten": []})
        new_card = {
            "id": f"kbv2-{uuid.uuid4().hex[:8]}",
            "begrip": begrip.strip(),
            "lade": None,
            "status": "draft",
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {},
            "tags": [],
            "verbanden": [],
            "footnote": {
                "bron": source,
                "ingedeeld_door": None,
                "ingedeeld_op": None,
                "vorige_versie_v1": None,
                "vertrouwen": 0.3,
                "aangemaakt_door": user_id,
                "aangemaakt_op": _now(),
            },
            "_inbox_reason": "missing_laag1",
        }
        inbox.setdefault("kaarten", []).append(new_card)
        save_json(_inbox_path(), inbox)
        # Index ook
        idx = load_json(_index_path(), default={"entries": {}})
        idx.setdefault("entries", {})[begrip.lower().strip()] = {
            "kaart_id": new_card["id"], "lade": None,
            "has_lagen": [], "last_updated": _now(),
        }
        save_json(_index_path(), idx)
    return {"success": True, "kaart": new_card, "existing": False}


def dedupe_inbox(dry_run: bool = False) -> Dict:
    """v6_kbv2_dedupe_001 — Verwijder kaarten uit inbox die elders bestaan.

    Verwijdert een inbox-kaart als:
      - Een lade-kaart bestaat met dezelfde `id`, OF
      - Een lade-kaart bestaat met hetzelfde (lowercased) `begrip` EN die lade-kaart
        heeft een ingevulde laag1 (dus is "echt" ingevuld, niet leeg)

    Returns count van verwijderde duplicaten.
    """
    inbox = load_json(_inbox_path(), default={"kaarten": []})
    inbox_cards = inbox.get("kaarten", [])

    # Index lade-cards: id + begrip-met-laag1
    lade_ids = set()
    lade_begrippen_filled = set()
    for L in LADES:
        ld = load_json(_lade_path(L), default={"kaarten": []})
        for k in ld.get("kaarten", []):
            kid = k.get("id")
            if kid:
                lade_ids.add(kid)
            lagen = k.get("lagen") or {}
            l1 = (lagen.get("laag1", "") if isinstance(lagen, dict) else "") or ""
            if l1.strip() and k.get("begrip"):
                lade_begrippen_filled.add((k["begrip"] or "").lower().strip())

    duplicates = []
    kept = []
    for c in inbox_cards:
        cid = c.get("id")
        cbegrip = (c.get("begrip") or "").lower().strip()
        if cid in lade_ids or (cbegrip and cbegrip in lade_begrippen_filled):
            duplicates.append({"id": cid, "begrip": c.get("begrip")})
        else:
            kept.append(c)

    if not dry_run and duplicates:
        inbox["kaarten"] = kept
        inbox.setdefault("metadata", {})["last_dedupe_at"] = _now()
        inbox["metadata"]["last_dedupe_removed"] = len(duplicates)
        inbox["card_count"] = len(kept)
        save_json(_inbox_path(), inbox)

    return {
        "success": True,
        "dry_run": dry_run,
        "removed": len(duplicates),
        "remaining_inbox": len(kept),
        "examples": duplicates[:20],
    }


# ---------------------------------------------------------------------------
# Graceful Fallback (#DeWillem principe)
# ---------------------------------------------------------------------------

def graceful_fallback(begrip: str) -> Optional[Dict]:
    """#DeWillem: stap-terug-en-geef-context i.p.v. 'ik weet het niet'.
    
    Strategie:
      1. Direct hit via index? → return kaart
      2. Geen direct hit → check buurkaarten (kaarten met overlappende tags) per lade
      3. Geen buurkaarten → return None (caller doet dan fallback-prompt
         "Ik ken nog geen X. Wil je dat ik dit leer?")
    """
    direct = find_by_begrip(begrip)
    if direct:
        return {"type": "direct", **direct}
    # Tokenize begrip-zoektermen
    tokens = {t.strip().lower() for t in begrip.replace(",", " ").split() if t.strip()}
    if not tokens:
        return None
    best: Optional[Dict] = None
    best_score = 0
    for lade in LADES:
        d = load_json(_lade_path(lade), default={"kaarten": []})
        for k in d.get("kaarten", []):
            tags = {(t or "").lower() for t in (k.get("tags") or [])}
            score = len(tokens & tags)
            if score > best_score:
                best = {"type": "neighbor", "kaart": k, "lade": lade, "overlap": score}
                best_score = score
    return best
