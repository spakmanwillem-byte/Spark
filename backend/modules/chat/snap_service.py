"""
Snap & NLP Service - Standalone (geen spaCy/Levenshtein nodig)

Functionaliteit:
1. Knowledge lookup: zoek begrippen in knowledge_base.json
2. Snap creatie: maak placeholder kaarten voor onbekende woorden
3. Zin snap: sla context zinnen op
4. Dubbele woorden check: voorkom duplicaten
5. Sentiment detectie: positief/negatief/neutraal
6. Commando detectie: help, dagboek, triggers etc.
"""
import re
import secrets
import uuid
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json
from modules.graph.sync_service import upsert_node_from_entry

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# v4_snap_dedupe_002 — ascii fold zodat 'joel' en 'joël' op dezelfde kaart matchen
import unicodedata as _ud
def _ascii_fold(s: str) -> str:
    if not s:
        return ""
    return "".join(c for c in _ud.normalize("NFD", s) if _ud.category(c) != "Mn")
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "learned_knowledge" / "knowledge_base.json"
KEYWORDS_FILE = DATA_DIR / "keywords.json"
TRIGGERS_FILE = DATA_DIR / "conversation_triggers.json"

# Nederlandse stopwoorden - niet opslaan als snap
STOPWOORDEN = {
    "de", "het", "een", "en", "van", "in", "is", "op", "dat", "die", "er",
    "te", "aan", "niet", "ook", "met", "voor", "maar", "om", "dan", "als",
    "hun", "nog", "bij", "na", "al", "wel", "geen", "uit", "tot", "over",
    "hem", "haar", "zou", "worden", "heeft", "had", "kan", "dit", "zo",
    "was", "ben", "ik", "je", "jij", "hij", "zij", "wij", "mij", "we",
    "ze", "wat", "wie", "hoe", "waar", "ja", "nee", "ok", "oké",
    "zijn", "zal", "wil", "moet", "mag", "doe", "gaat", "komt", "heb",
    "meer", "veel", "heel", "erg", "best", "mooi", "goed", "cool",
    "slecht", "leuk", "fijn", "lekker", "naar", "even", "toch", "dus",
    "want", "omdat", "toen", "hier", "daar", "alles", "iets", "niks",
    "nooit", "altijd", "soms", "vaak", "weer", "eens", "twee", "drie",
    "echt", "heel", "super", "gewoon", "alleen", "samen", "graag",
    "nieuwe", "andere", "eigen", "grote", "kleine", "lang", "kort",
    "mijn", "jouw", "zijn", "haar", "ons", "onze", "hun", "welke",
    "deze", "die", "dit", "dat", "elk", "elke", "alle", "beide",
    "uitleg", "voorbeeld", "informatie", "info", "bedoel", "bedoelt",
    "vergelijk", "vergelijken", "verklaar", "verklaren", "beschrijf",
    "weet", "weten", "denk", "denken", "vind", "vinden", "lijkt",
    "maak", "maken", "geef", "geven", "krijg", "krijgen", "neem",
}


class SnapNLPService:
    def __init__(self):
        self._keywords = None
        self._triggers = None
        self._knowledge_cache = None
        self._knowledge_index = None

    @property
    def keywords(self):
        if self._keywords is None:
            self._keywords = load_json(KEYWORDS_FILE, default={})
        return self._keywords

    @property
    def triggers(self):
        if self._triggers is None:
            self._triggers = load_json(TRIGGERS_FILE, default={})
        return self._triggers

    def _load_knowledge(self):
        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        return data.get("knowledge_entries", [])

    def _build_index(self, entries):
        """Bouw een snelle lookup index op begrip (lowercase).
        v4_snap_dedupe_002: dubbele index op zowel ruwe als ascii-genormaliseerde begrip
        zodat 'joel' en 'joël' op dezelfde kaarten matchen."""
        index = {}
        for e in entries:
            tags = e.get("tags") or []
            if "context-zin" in tags or (e.get("metadata") or {}).get("is_sentence"):
                continue
            begrip = (e.get("begrip") or "").lower().strip()
            if begrip:
                keys = {begrip, _ascii_fold(begrip)}
                for k in keys:
                    if k:
                        index.setdefault(k, []).append(e)
        return index

    def _get_index(self):
        if self._knowledge_index is None:
            entries = self._load_knowledge()
            self._knowledge_index = self._build_index(entries)
        return self._knowledge_index

    def invalidate_cache(self):
        """Call na save/delete operaties"""
        self._knowledge_index = None
        self._knowledge_cache = None

    # ========== KNOWLEDGE LOOKUP ==========

    def lookup(self, query):
        """
        Zoek een begrip in de kennisbank.
        Geeft de beste match terug met lagen antwoord.
        """
        index = self._get_index()
        q = query.lower().strip()

        # 1. Exacte match (incl. ascii-fold fallback voor umlaut/accenten — v4_snap_dedupe_002)
        if q in index:
            matches = index[q]
            best = max(matches, key=lambda e: e.get("belangrijkheid", 0))
            return self._format_result(best, "exact")
        q_fold = _ascii_fold(q)
        if q_fold != q and q_fold in index:
            matches = index[q_fold]
            best = max(matches, key=lambda e: e.get("belangrijkheid", 0))
            return self._format_result(best, "exact")

        # 2. Woorden uit de zin matchen
        words = self._extract_meaningful_words(q)
        found = []
        for w in words:
            w_fold = _ascii_fold(w)
            for k in (w, w_fold) if w_fold != w else (w,):
                if k in index:
                    for entry in index[k]:
                        found.append((w, entry))
                    break

        if found:
            # Sorteer op belangrijkheid
            found.sort(key=lambda x: x[1].get("belangrijkheid", 0), reverse=True)
            best_word, best_entry = found[0]
            return self._format_result(best_entry, "word_match", matched_word=best_word)

        # 3. Startswith zoeken (strikter dan substring)
        if len(q) >= 5:
            for begrip, entries in index.items():
                if len(begrip) >= 5 and (begrip.startswith(q) or q.startswith(begrip)):
                    return self._format_result(entries[0], "partial")

        return None

    def multi_lookup(self, text):
        """
        Zoek ALLE begrippen die in een zin voorkomen.
        Retourneert lijst van matches.
        """
        index = self._get_index()
        words = self._extract_meaningful_words(text.lower())
        results = []
        seen = set()

        for w in words:
            if w in index and w not in seen:
                seen.add(w)
                best = max(index[w], key=lambda e: e.get("belangrijkheid", 0))
                results.append(self._format_result(best, "word_match", matched_word=w))
            elif w not in seen:
                # Substring match
                found = self._find_in_index(w, index)
                if found:
                    seen.add(w)
                    best = max(found, key=lambda e: e.get("belangrijkheid", 0))
                    results.append(self._format_result(best, "partial", matched_word=w))

        return results

    def _format_result(self, entry, match_type, matched_word=None):
        lagen = entry.get("lagen", {}) or {}
        # NL keys na migratie
        ws5 = entry.get("ws5", {}) or {}
        return {
            "id": entry.get("id"),
            "begrip": entry.get("begrip"),
            "laag1": lagen.get("laag1", ""),
            "laag2": lagen.get("laag2", ""),
            "laag3": lagen.get("laag3", ""),
            "laag4": lagen.get("laag4", ""),
            "topic": entry.get("topic", ""),
            "tags": entry.get("tags", []),
            "belangrijkheid": entry.get("belangrijkheid", 0),
            "match_type": match_type,
            "matched_word": matched_word,
            "context_5wh": {
                "wie": ws5.get("wie", ""),
                "wat": ws5.get("wat", ""),
                "waar": ws5.get("waar", ""),
                "wanneer": ws5.get("wanneer", ""),
                "waarom": ws5.get("waarom", ""),
                "hoe": ws5.get("hoe", ""),
            },
        }

    # ========== DEEP LAYERS & SENTENCE-SNAP MATCH (v4_011) ==========

    def get_entry_by_id(self, entry_id):
        """Haal een kaart op id uit de kennisbank."""
        if not entry_id:
            return None
        entries = self._load_knowledge()
        for e in entries:
            if e.get("id") == entry_id:
                return e
        return None

    def get_layer(self, entry, depth):
        """Geef de tekst van een specifieke laag terug (laag1..laag4).
        Fallback-keten: als gevraagde laag leeg is, val terug op de hoogste
        wèl-gevulde laag <= depth. Geeft tuple (laag_nr, tekst, fallback_used)."""
        if not entry:
            return (depth, "", False)
        lagen = entry.get("lagen", {}) or {}
        depth = max(1, min(int(depth or 1), 4))
        key = f"laag{depth}"
        text = (lagen.get(key) or "").strip()
        if text:
            return (depth, text, False)
        # Fallback: hoogste lagere laag die wel inhoud heeft
        for d in range(depth - 1, 0, -1):
            t = (lagen.get(f"laag{d}") or "").strip()
            if t:
                return (d, t, True)
        return (depth, "", False)

    def detect_deeper_request(self, text):
        """Detecteer of user vraagt om een DIEPERE uitleg van het laatste begrip.

        Geeft None of een int (gevraagde laag 2..4) terug.
        - 'vertel meer', 'meer info', 'leg dieper uit', 'verdieping' → +1 t.o.v. huidig
        - 'laag 2/3/4', 'tweede/derde/vierde laag' → expliciete diepte
        """
        t = text.lower().strip()
        # Expliciete laag-nummers
        explicit = {
            "laag 2": 2, "laag 3": 3, "laag 4": 4,
            "tweede laag": 2, "derde laag": 3, "vierde laag": 4,
            "laag2": 2, "laag3": 3, "laag4": 4,
        }
        for key, lvl in explicit.items():
            if key in t:
                return lvl
        # Generieke "dieper / meer" triggers → +1 vanaf huidige laag (door caller toegepast)
        deeper_patterns = [
            "vertel meer", "vertel me meer", "meer info", "meer informatie",
            "meer hierover", "meer over dit", "meer over dat",
            "leg dieper uit", "leg uit dieper", "dieper uitleggen", "dieper uit",
            "diepere uitleg", "diepere betekenis", "diepere context",
            "verdieping", "verdiep", "uitgebreidere uitleg", "uitgebreider",
            "ga dieper", "vertel meer hierover", "vertel verder",
            "leg meer uit", "wat nog meer", "ga verder",
        ]
        for p in deeper_patterns:
            if p in t:
                return -1  # signaal: +1 t.o.v. huidige diepte
        return None

    def lookup_sentence_match(self, text, min_overlap=2, min_ratio=0.5):
        """Fuzzy match op `context-zin` snaps via woord-overlap.

        Geeft beste sentence-snap entry terug die gevulde lagen heeft.
        Vereisten:
        - minimaal `min_overlap` betekenisvolle woorden gedeeld
        - overlap-ratio (gedeelde/totaal in user-tekst) >= min_ratio
        - de sentence-snap heeft minstens één laag gevuld
        """
        entries = self._load_knowledge()
        user_words = set(self._extract_meaningful_words(text))
        if len(user_words) < min_overlap:
            return None
        best = None
        best_score = 0
        for e in entries:
            tags = e.get("tags") or []
            is_sent = "context-zin" in tags or (e.get("metadata") or {}).get("is_sentence")
            if not is_sent:
                continue
            lagen = e.get("lagen", {}) or {}
            if not any((lagen.get(k) or "").strip() for k in ("laag1", "laag2", "laag3", "laag4")):
                continue
            sent_words = set(self._extract_meaningful_words(e.get("begrip", "")))
            if not sent_words:
                continue
            overlap = user_words & sent_words
            if len(overlap) < min_overlap:
                continue
            ratio = len(overlap) / max(1, len(user_words))
            if ratio < min_ratio:
                continue
            score = len(overlap) * 10 + (e.get("belangrijkheid", 0) or 0)
            if score > best_score:
                best_score = score
                best = e
        if not best:
            return None
        return self._format_result(best, "sentence_match", matched_word=None)

    def _extract_meaningful_words(self, text):
        """Haal betekenisvolle woorden uit tekst (geen stopwoorden)"""
        words = re.findall(r'\b[a-zA-Zéèêëïüöà]+\b', text.lower())
        return [w for w in words if w not in STOPWOORDEN and len(w) > 2]

    def _find_in_index(self, word, index):
        """Zoek een woord in de index - alleen als het woord het begin van het begrip is of exact matcht"""
        # Exact match
        if word in index:
            return index[word]
        # Partial match: ALLEEN als BEIDE woord en begrip minstens 5 chars zijn
        # (voorkomt dat "SUI" matcht op "suikerspin", of "Gist" op "gisteren")
        if len(word) >= 5:
            for begrip, entries in index.items():
                if len(begrip) >= 5 and (begrip.startswith(word) or word.startswith(begrip)):
                    return entries
        return None

    # ========== SNAP CREATION ==========

    def create_word_snap(self, concept, context, user_naam, extra_tags=None, decomposed_from=None):
        """
        Maak een woord-snap: placeholder kaart voor onbekend begrip.
        Checkt duplicaten. Retourneert None als het al bestaat of een stopwoord is.

        extra_tags: extra tags die overgeërfd worden (bv. van decompositie)
        decomposed_from: list van begrippen waar dit woord uit is afgeleid
        """
        concept = concept.strip()
        if not concept or len(concept) < 2:
            return None

        # Stopwoord check
        if concept.lower() in STOPWOORDEN:
            return None

        # Duplicate check (exact + ascii-fold voor accenten/umlaut — v4_snap_dedupe_002)
        index = self._get_index()
        if concept.lower() in index:
            return None
        concept_fold = _ascii_fold(concept.lower())
        if concept_fold != concept.lower() and concept_fold in index:
            return None

        tags = ["knowledge-snap", "auto-generated"]
        if extra_tags:
            for t in extra_tags:
                if t and t not in tags:
                    tags.append(t)
        if decomposed_from:
            tags.append("compositional")

        # Maak snap entry (zelfde structuur als oude systeem)
        entry = {
            "id": f"snap-{uuid.uuid4().hex[:8]}",
            "begrip": concept,
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
            "tags": tags,
            "bron": "auto-detected",
            "detected_by": user_naam,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "belangrijkheid": 3,
            "usage_count": 0,
            "topic": "",
            "snap_context": context[:200] if context else "",
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_via": "snap",
                "is_sentence": False,
                **({"decomposed_from": decomposed_from} if decomposed_from else {}),
            },
        }

        # Opslaan
        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        data["knowledge_entries"].append(entry)
        save_json(KNOWLEDGE_FILE, data)
        self.invalidate_cache()

        # Graph auto-sync: voeg node toe + bereken edges via shared tags
        try:
            upsert_node_from_entry(entry)
        except Exception as ex:
            print(f"[graph-sync] word-snap upsert failed: {ex}")

        return entry

    def create_sentence_snap(self, sentence, context, user_naam):
        """
        Maak een zin-snap: context zin opslaan (geen duplicate check behalve exact).
        """
        sentence = sentence.strip()
        if not sentence or len(sentence) < 5:
            return None

        # Alleen exacte duplicate check
        index = self._get_index()
        if sentence.lower() in index:
            return None

        entry = {
            "id": f"snap-{uuid.uuid4().hex[:8]}",
            "begrip": sentence,
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
            "tags": ["knowledge-snap", "auto-generated", "context-zin"],
            "bron": "auto-detected",
            "detected_by": user_naam,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "belangrijkheid": 2,
            "usage_count": 0,
            "topic": "",
            "snap_context": context[:200] if context else "",
            "metadata": {"created_at": datetime.now(timezone.utc).isoformat(), "created_via": "snap", "is_sentence": True},
        }

        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        data["knowledge_entries"].append(entry)
        save_json(KNOWLEDGE_FILE, data)
        self.invalidate_cache()

        # Graph auto-sync
        try:
            upsert_node_from_entry(entry)
        except Exception as ex:
            print(f"[graph-sync] sentence-snap upsert failed: {ex}")

        return entry

    # ========== SENTIMENT & TRIGGERS ==========

    def detect_sentiment(self, text):
        text_lower = text.lower()
        pos_words = self.keywords.get("emoties", {}).get("woorden", {}).get("positief", [])
        neg_words = self.keywords.get("emoties", {}).get("woorden", {}).get("negatief", [])
        pos = sum(1 for w in pos_words if w in text_lower)
        neg = sum(1 for w in neg_words if w in text_lower)
        if pos > neg:
            return "positief"
        elif neg > pos:
            return "negatief"
        return "neutraal"

    def detect_greeting(self, text):
        text_lower = text.lower().strip()
        greetings = self.triggers.get("greeting", {}).get("triggers", [])
        words = set(re.findall(r'\b\w+\b', text_lower))
        return any(g in words for g in greetings)

    def detect_thanks(self, text):
        text_lower = text.lower().strip()
        thanks = self.triggers.get("thanks", {}).get("triggers", [])
        words = set(re.findall(r'\b\w+\b', text_lower))
        return any(t in words for t in thanks)

    def detect_goodbye(self, text):
        text_lower = text.lower().strip()
        byes = self.triggers.get("goodbye", {}).get("triggers", [])
        words = set(re.findall(r'\b\w+\b', text_lower))
        return any(b in words for b in byes)

    def detect_how_are_you(self, text):
        text_lower = text.lower().strip()
        triggers = self.triggers.get("how_are_you", {}).get("triggers", [])
        # Multi-word triggers need substring match, single words need word boundary
        for t in triggers:
            if ' ' in t:
                if t in text_lower:
                    return True
            else:
                words = set(re.findall(r'\b\w+\b', text_lower))
                if t in words:
                    return True
        return False

    def detect_self_state(self, text):
        """
        Detecteer of user specifiek vraagt hoe het met SPARK/JOU gaat.
        Specifieker dan how_are_you (die ook 'alles goed?' generiek vangt).
        """
        text_lower = text.lower().strip()
        triggers = self.triggers.get("self_state", {}).get("triggers", [])
        for t in triggers:
            if t in text_lower:
                return True
        return False

    def detect_rejection(self, text):
        """Detecteer of user 'nee dat bedoel ik niet' zegt."""
        text_lower = text.lower().strip()
        triggers = self.triggers.get("rejection", {}).get("triggers", [])
        for t in triggers:
            if ' ' in t:
                if t in text_lower:
                    return True
            else:
                words = set(re.findall(r'\b\w+\b', text_lower))
                if t in words:
                    return True
        return False

    def detect_confirmation(self, text):
        """Detecteer of user 'ja/jep/klopt' zegt (korte bevestiging)."""
        text_lower = text.lower().strip()
        # Whole-message match voor korte bevestigingen
        triggers = self.triggers.get("confirmation", {}).get("triggers", [])
        # Sanitize: strip punctuation aan einde
        stripped = re.sub(r'[.!?,\s]+$', '', text_lower)
        if stripped in triggers:
            return True
        # Ook substring match voor korte berichten ('<=30 chars)
        if len(text_lower) <= 30:
            words = set(re.findall(r'\b\w+\b', text_lower))
            if any(t in words for t in triggers if ' ' not in t):
                return True
        return False

    def create_homonym_variant(self, begrip, user_naam, original_id=None):
        """
        Maak een duplicate snap voor een bestaand begrip (homoniem).
        Geeft de nieuwe kaart een 'homonym_variant' tag + link naar origineel.
        """
        entry = {
            "id": f"snap-{uuid.uuid4().hex[:8]}",
            "begrip": begrip,
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""},
            "tags": ["knowledge-snap", "homonym_variant", "auto-generated"],
            "bron": "homonym-disambiguation",
            "detected_by": user_naam,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "belangrijkheid": 2,
            "usage_count": 0,
            "topic": "",
            "snap_context": f"Homoniem van '{begrip}' — user gaf aan andere betekenis te bedoelen",
            "related_to": original_id,
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_via": "homonym_flow",
                "is_sentence": False,
            },
        }
        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        data["knowledge_entries"].append(entry)
        save_json(KNOWLEDGE_FILE, data)
        self.invalidate_cache()

        # Graph auto-sync (homonym variant — krijgt sterke 'homonym_variant' edge)
        try:
            upsert_node_from_entry(entry)
        except Exception as ex:
            print(f"[graph-sync] homonym-variant upsert failed: {ex}")

        return entry

    def get_trigger_response(self, trigger_type):
        """Geeft een random response voor een trigger type"""
        import random
        responses = self.triggers.get(trigger_type, {}).get("responses", [])
        return secrets.choice(responses) if responses else None

    def is_question(self, text):
        text_lower = text.lower()
        vraag_woorden = self.keywords.get("vragen", {}).get("woorden", [])
        return any(w in text_lower for w in vraag_woorden) or text.strip().endswith('?')
