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
import uuid
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
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
        """Bouw een snelle lookup index op begrip (lowercase)"""
        index = {}
        for e in entries:
            begrip = (e.get("begrip") or "").lower().strip()
            if begrip:
                if begrip not in index:
                    index[begrip] = []
                index[begrip].append(e)
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

        # 1. Exacte match
        if q in index:
            matches = index[q]
            best = max(matches, key=lambda e: e.get("belangrijkheid", 0))
            return self._format_result(best, "exact")

        # 2. Woorden uit de zin matchen
        words = self._extract_meaningful_words(q)
        found = []
        for w in words:
            if w in index:
                for entry in index[w]:
                    found.append((w, entry))

        if found:
            # Sorteer op belangrijkheid
            found.sort(key=lambda x: x[1].get("belangrijkheid", 0), reverse=True)
            best_word, best_entry = found[0]
            return self._format_result(best_entry, "word_match", matched_word=best_word)

        # 3. Startswith zoeken (strikter dan substring)
        if len(q) >= 5:
            for begrip, entries in index.items():
                if begrip.startswith(q) or q.startswith(begrip):
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
        wh = entry.get("context_5wh", {}) or {}
        return {
            "id": entry.get("id"),
            "begrip": entry.get("begrip"),
            "laag1": lagen.get("laag1", ""),
            "laag2": lagen.get("laag2", ""),
            "laag3": lagen.get("laag3", ""),
            "topic": entry.get("topic", ""),
            "tags": entry.get("tags", []),
            "belangrijkheid": entry.get("belangrijkheid", 0),
            "match_type": match_type,
            "matched_word": matched_word,
            "context_5wh": {
                "wie": wh.get("wie", ""),
                "wat": wh.get("wat", ""),
                "waar": wh.get("waar", ""),
                "wanneer": wh.get("wanneer", ""),
                "waarom": wh.get("waarom", ""),
                "hoe": wh.get("hoe", ""),
            },
        }

    def _extract_meaningful_words(self, text):
        """Haal betekenisvolle woorden uit tekst (geen stopwoorden)"""
        words = re.findall(r'\b[a-zA-Zéèêëïüöà]+\b', text.lower())
        return [w for w in words if w not in STOPWOORDEN and len(w) > 2]

    def _find_in_index(self, word, index):
        """Zoek een woord in de index - alleen als het woord het begin van het begrip is of exact matcht"""
        # Exact match
        if word in index:
            return index[word]
        # Alleen matchen als het woord minimaal 5 chars is EN het begrip ermee begint
        if len(word) >= 5:
            for begrip, entries in index.items():
                if begrip.startswith(word) or word.startswith(begrip):
                    return entries
        return None

    # ========== SNAP CREATION ==========

    def create_word_snap(self, concept, context, user_naam):
        """
        Maak een woord-snap: placeholder kaart voor onbekend begrip.
        Checkt duplicaten. Retourneert None als het al bestaat of een stopwoord is.
        """
        concept = concept.strip()
        if not concept or len(concept) < 2:
            return None

        # Stopwoord check
        if concept.lower() in STOPWOORDEN:
            return None

        # Duplicate check (exact)
        index = self._get_index()
        if concept.lower() in index:
            return None

        # Maak snap entry (zelfde structuur als oude systeem)
        entry = {
            "id": f"snap-{uuid.uuid4().hex[:8]}",
            "begrip": concept,
            "lagen": {"laag1": "", "laag2": "", "laag3": "", "laag4": ""},
            "ws5": {"who": "", "what": "", "when": "", "where": "", "why": "", "how": ""},
            "tags": ["knowledge-snap", "auto-generated"],
            "bron": "auto-detected",
            "detected_by": user_naam,
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "belangrijkheid": 3,
            "usage_count": 0,
            "topic": "",
            "snap_context": context[:200] if context else "",
            "metadata": {"created_at": datetime.now(timezone.utc).isoformat(), "created_via": "snap", "is_sentence": False},
        }

        # Opslaan
        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        data["knowledge_entries"].append(entry)
        save_json(KNOWLEDGE_FILE, data)
        self.invalidate_cache()

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
            "ws5": {"who": "", "what": "", "when": "", "where": "", "why": "", "how": ""},
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

    def get_trigger_response(self, trigger_type):
        """Geeft een random response voor een trigger type"""
        import random
        responses = self.triggers.get(trigger_type, {}).get("responses", [])
        return random.choice(responses) if responses else None

    def is_question(self, text):
        text_lower = text.lower()
        vraag_woorden = self.keywords.get("vragen", {}).get("woorden", [])
        return any(w in text_lower for w in vraag_woorden) or text.strip().endswith('?')
