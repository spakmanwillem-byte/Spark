"""
Emotie Detectie Service - Hybride systeem
1. STATIC: Hard-coded triggers uit emotion_triggers.json
2. DYNAMIC: Leert van knowledge cards met #emotie-* tags

4 Basis Emoties: Blij, Boos, Bang, Bedroefd
Anti-misbruik: Elk woord max 3x per bericht
"""
import secrets
from pathlib import Path
from collections import Counter
from modules.core.storage import load_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
TRIGGERS_FILE = DATA_DIR / "emotions" / "emotion_triggers.json"
SPARK_EMOTIONS_FILE = DATA_DIR / "emotions" / "spark_emotions.json"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "learned_knowledge" / "knowledge_base.json"


class EmotionDetectionService:
    _triggers_cache = None
    _learned_cache = None
    _learned_cache_time = 0

    @staticmethod
    def _load_triggers():
        if EmotionDetectionService._triggers_cache is None:
            EmotionDetectionService._triggers_cache = load_json(TRIGGERS_FILE, default={"emotions": {}})
        return EmotionDetectionService._triggers_cache

    @staticmethod
    def _load_learned_triggers():
        """Laad geleerde emotie triggers uit knowledge cards met emotie-tags.

        Ondersteunt drie tag-patronen:
        1. Single tag: 'emotie-blij' / '#emotie-blij' (oude stijl)
        2. Combo tag : 'emotie blij' (één tag met spatie)
        3. Twee losse tags: 'emotie' + 'blij' op dezelfde kaart (user-stijl v4_011)
        Geldige emoties: blij, boos, bang, bedroefd, neutraal.
        """
        import time
        now = time.time()
        if (EmotionDetectionService._learned_cache and
                now - EmotionDetectionService._learned_cache_time < 60):
            return EmotionDetectionService._learned_cache

        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        entries = data.get("knowledge_entries", [])

        learned = {"blij": {}, "boos": {}, "bang": {}, "bedroefd": {}, "neutraal": {}}
        valid_emotions = set(learned.keys())
        emotie_map = {
            "emotie-blij": "blij", "#emotie-blij": "blij",
            "emotie-boos": "boos", "#emotie-boos": "boos",
            "emotie-bang": "bang", "#emotie-bang": "bang",
            "emotie-bedroefd": "bedroefd", "#emotie-bedroefd": "bedroefd",
            "emotie-neutraal": "neutraal", "#emotie-neutraal": "neutraal",
            "emotie blij": "blij", "emotie boos": "boos", "emotie bang": "bang",
            "emotie bedroefd": "bedroefd", "emotie neutraal": "neutraal",
        }

        for entry in entries:
            # Geen status-filter meer — draft kaarten tellen ook mee voor leren
            begrip = (entry.get("begrip") or "").lower().strip()
            if not begrip:
                continue
            tag_set = set()
            for tag in entry.get("tags", []) or []:
                tag_set.add(tag.lower().strip().lstrip("#").strip())
            matched_emotion = None
            for tag in tag_set:
                if tag in emotie_map:
                    matched_emotion = emotie_map[tag]
                    break
            # Patroon 3: losse 'emotie' + één van de 5 emotie-namen
            if not matched_emotion and "emotie" in tag_set:
                for em in valid_emotions:
                    if em in tag_set:
                        matched_emotion = em
                        break
            if matched_emotion:
                learned[matched_emotion][begrip] = 3

        EmotionDetectionService._learned_cache = learned
        EmotionDetectionService._learned_cache_time = now
        return learned

    @staticmethod
    def detect_emotion(message):
        """Detecteer emotie in bericht - hybride (static + learned)"""
        triggers_data = EmotionDetectionService._load_triggers()
        learned = EmotionDetectionService._load_learned_triggers()
        emotions = triggers_data.get("emotions", {})
        max_word_count = 3
        min_score = 3

        msg_lower = message.lower()
        word_freq = Counter(msg_lower.split())

        scores = {}
        for emo_name, emo_data in emotions.items():
            score = 0
            triggered = []
            sources = set()

            # Static triggers
            for word, points in emo_data.get("triggers", {}).items():
                if word in msg_lower:
                    occ = min(word_freq.get(word, 0), max_word_count)
                    if occ > 0:
                        score += points * occ
                        triggered.append(word)
                        sources.add("static")

            # Learned triggers
            for word, points in learned.get(emo_name, {}).items():
                if word in msg_lower:
                    occ = min(word_freq.get(word, 0), max_word_count)
                    if occ > 0:
                        score += points * occ
                        if word not in triggered:
                            triggered.append(word)
                        sources.add("learned")

            if score > 0:
                source = "both" if len(sources) == 2 else ("learned" if "learned" in sources else "static")
                scores[emo_name] = {
                    "score": score, "triggered_words": triggered,
                    "source": source, "emoji": emo_data.get("emoji", ""),
                    "color": emo_data.get("color", ""),
                }

        if not scores:
            return None

        dominant = max(scores.items(), key=lambda x: x[1]["score"])
        emo_name, info = dominant
        if info["score"] < min_score:
            return None

        s = info["score"]
        intensity = min(0.3 + (s / 5) * 0.2, 1.0) if s <= 5 else min(0.5 + ((s - 5) / 5) * 0.2, 1.0) if s <= 10 else min(0.7 + ((s - 10) / 10) * 0.3, 1.0)

        empathic = triggers_data.get("empathic_responses", {}).get(emo_name, [])
        return {
            "emotion": emo_name,
            "score": s,
            "intensity": round(intensity, 2),
            "triggered_words": info["triggered_words"],
            "source": info["source"],
            "emoji": info["emoji"],
            "color": info["color"],
            "empathic_response": secrets.choice(empathic) if empathic else None,
        }

    @staticmethod
    def get_spark_state():
        """Haal Spark's huidige emotionele staat op"""
        data = load_json(SPARK_EMOTIONS_FILE, default={})
        return data.get("current_emotion", {"state": "neutral", "intensity": 0.5})

    @staticmethod
    def get_spark_emotions():
        """Haal alle Spark emotie definities op"""
        return load_json(SPARK_EMOTIONS_FILE, default={})

    @staticmethod
    def get_learned_counts():
        """Hoeveel geleerde emotie woorden per type"""
        learned = EmotionDetectionService._load_learned_triggers()
        return {k: len(v) for k, v in learned.items()}
