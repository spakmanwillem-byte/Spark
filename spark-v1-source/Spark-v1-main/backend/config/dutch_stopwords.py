"""
Nederlandse stopwords en filter configuratie voor knowledge snap systeem
Doel: Alleen betekenisvolle concepten opslaan, geen grammaticale ruis
"""

import re
from typing import Optional, Tuple

# Lidwoorden
LIDWOORDEN = {
    "de", "het", "een", "'t", "d'r"
}

# Opvulwoorden die uit concepten gefilterd moeten worden
FILLER_WORDS = {
    "eigenlijk", "precies", "nou", "dan", "toch", "gewoon", "zo", 
    "even", "eens", "maar", "hoor", "zeg", "hè"
}


# ====================
# CONCEPT EXTRACTION
# ====================

def _remove_filler_words(text: str) -> str:
    """
    Remove filler words from the end of extracted concepts
    
    Examples:
        "kunstmatige intelligentie eigenlijk" → "kunstmatige intelligentie"
        "blockchain precies" → "blockchain"
    """
    words = text.split()
    while words and words[-1] in FILLER_WORDS:
        words.pop()
    return ' '.join(words)


def _has_meaning(text: str) -> bool:
    """
    Check if text has meaning: actie, emotie, intentie, or mening
    
    This is Willem's snap detection - check for MEANING, not fixed words.
    
    Examples that SHOULD pass:
        "ik ga slapen" → actie (gaan)
        "dat voelt niet goed" → emotie (voelen)
        "ik ben het hier niet mee eens" → mening (zijn + eens)
        "jij snapt me niet" → actie (snappen)
        "de hond loopt" → actie (lopen)
    
    Returns:
        True if sentence has meaning, False otherwise
    """
    text_lower = text.lower()
    
    # Common action verbs (werkwoorden)
    action_verbs = {
        'ga', 'gaan', 'loop', 'lopen', 'werk', 'werken', 'maak', 'maken', 
        'doe', 'doen', 'zie', 'zien', 'hoor', 'horen', 'weet', 'weten',
        'snap', 'snappen', 'begrijp', 'begrijpen', 'lees', 'lezen',
        'schrijf', 'schrijven', 'speel', 'spelen', 'kijk', 'kijken',
        'eet', 'eten', 'drink', 'drinken', 'slaap', 'slapen',
        'kom', 'komen', 'blijf', 'blijven', 'help', 'helpen',
        'probeer', 'proberen', 'zeg', 'zeggen', 'vraag', 'vragen'
    }
    
    # Emotion words (gevoelswoorden)
    emotion_words = {
        'voel', 'voelt', 'voelen', 'ben', 'bent', 'zijn', 'was', 'waren',
        'blij', 'verdrietig', 'boos', 'bang', 'gelukkig', 'ongelukkig',
        'fijn', 'leuk', 'goed', 'slecht', 'naar', 'prettig',
        'houd', 'hou', 'houden', 'haat', 'liefde', 'liefhebben'
    }
    
    # Intention words (intentiewoorden)
    intention_words = {
        'wil', 'wilt', 'willen', 'moet', 'moeten', 'kan', 'kunnen',
        'mag', 'mogen', 'zou', 'zouden', 'hoef', 'hoeven',
        'probeer', 'proberen', 'plan', 'plannen'
    }
    
    # Opinion words (meningswoorden)
    opinion_words = {
        'vind', 'vindt', 'vinden', 'denk', 'denkt', 'denken',
        'geloof', 'gelooft', 'geloven', 'meen', 'meent', 'menen',
        'eens', 'oneens', 'akkoord', 'snap', 'snappen'
    }
    
    # Check if any meaningful word is present
    words = text_lower.split()
    for word in words:
        # Remove common suffixes for verb matching
        word_stem = word.rstrip('t').rstrip('en')
        
        if word in action_verbs or word_stem in action_verbs:
            return True
        if word in emotion_words or word_stem in emotion_words:
            return True
        if word in intention_words or word_stem in intention_words:
            return True
        if word in opinion_words or word_stem in opinion_words:
            return True
    
    return False


def extract_concept_from_input(text: str) -> Optional[str]:
    """
    Extract the core concept from user input (question, statement, phrase)
    
    Examples:
        "Wat is een auto?" → "auto"
        "Vertel over blockchain" → "blockchain"
        "Wie is tijd" → "tijd"
        "Hoe werkt fotosynthese?" → "fotosynthese"
    
    Returns:
        Extracted concept or None if no concept found
    """
    if not text or not isinstance(text, str):
        return None
    
    # Clean input
    text = text.strip().rstrip('?!.')
    text_lower = text.lower()
    
    # Pattern 1: "Wat is [een/de] [X]?" → X
    match = re.search(r'wat is (?:een |de |het )?(.+)', text_lower)
    if match:
        concept = match.group(1).strip()
        return _remove_filler_words(concept)
    
    # Pattern 2: "Wie is [X]?" → X
    match = re.search(r'wie is (.+)', text_lower)
    if match:
        concept = match.group(1).strip()
        return _remove_filler_words(concept)
    
    # Pattern 3: "Waar is [X]?" → X
    match = re.search(r'waar is (.+)', text_lower)
    if match:
        concept = match.group(1).strip()
        return _remove_filler_words(concept)
    
    # Pattern 4: "Waarom is [X]?" → X
    match = re.search(r'waarom is (.+)', text_lower)
    if match:
        concept = match.group(1).strip()
        return _remove_filler_words(concept)
    
    # Pattern 5: "Hoe werkt [X]?" → X (remove trailing words like "precies")
    match = re.search(r'hoe werkt (.+)', text_lower)
    if match:
        concept = match.group(1).strip()
        return _remove_filler_words(concept)
    
    # Pattern 6: "Vertel [me] [meer] over [X]" → X
    match = re.search(r'vertel (?:me )?(?:meer )?over (.+)', text_lower)
    if match:
        concept = match.group(1).strip()
        return _remove_filler_words(concept)
    
    # Pattern 7: "Leg uit wat [X] is" → X
    match = re.search(r'leg uit wat (.+) is', text_lower)
    if match:
        concept = match.group(1).strip()
        return _remove_filler_words(concept)
    
    # Pattern 8: Questions are also valid snaps (context)
    # "wat is werk", "waarom voel ik dit", "hoe werkt dit"
    if text_lower.startswith(('wat ', 'wie ', 'waar ', 'waarom ', 'hoe ', 'wanneer ')):
        # Keep the full question as context snap
        return text
    
    # Pattern 9: MEANINGFUL STATEMENT DETECTION (betekenis-check, niet beginwoorden!)
    # Check if sentence has meaning: actie, emotie, intentie, mening
    words = text.split()
    
    # Single/few words → likely a concept
    if len(words) <= 3:
        return text
    
    # Longer statements → check for meaning (up to 15 words)
    if len(words) <= 15:
        if _has_meaning(text_lower):
            return text
    
    # Too long or no meaning
    return None


def normalize_concept(concept: str) -> str:
    """
    Normalize concept to standard format
    
    Examples:
        "een auto" → "Auto"
        "de appel" → "Appel"
        "  blockchain  " → "Blockchain"
        "AuTo" → "Auto"
    
    Rules:
        1. Remove leading articles (de, het, een)
        2. Strip whitespace
        3. Capitalize first letter
    """
    if not concept:
        return concept
    
    # Remove articles at start
    concept = re.sub(r'^(de|het|een)\s+', '', concept, flags=re.IGNORECASE)
    
    # Strip whitespace
    concept = concept.strip()
    
    # Capitalize first letter only (rest stays as-is for acronyms like "DNA")
    if concept:
        concept = concept[0].upper() + concept[1:]
    
    return concept


# Voorzetsels
VOORZETSELS = {
    "van", "in", "op", "naar", "met", "voor", "door", "uit", "aan", "bij",
    "tot", "over", "onder", "tussen", "achter", "naast", "tegen", "zonder",
    "binnen", "buiten", "rond", "rondom", "om", "per", "via", "sinds", "gedurende"
}

# Voegwoorden
VOEGWOORDEN = {
    "en", "maar", "of", "want", "omdat", "dus", "als", "dan", "dat", "zodat",
    "terwijl", "hoewel", "ofschoon", "aangezien", "tenzij", "mits", "indien"
}

# Voornaamwoorden
VOORNAAMWOORDEN = {
    "ik", "jij", "je", "hij", "zij", "ze", "wij", "we", "jullie", "u",
    "mij", "me", "jou", "hem", "haar", "ons", "hun", "hen",
    "dit", "dat", "deze", "die", "dit", "zulke", "dergelijke",
    "men", "iemand", "niemand", "iets", "niets", "alles", "elk", "elke",
    "al", "beide", "sommige", "enkele", "vele", "meer", "minder", "weinig"
}

# Hulpwerkwoorden
HULPWERKWOORDEN = {
    "zijn", "ben", "bent", "is", "was", "waren", "geweest", "zijn",
    "hebben", "heb", "hebt", "heeft", "had", "hadden", "gehad",
    "worden", "word", "wordt", "werd", "werden", "geworden",
    "zullen", "zal", "zou", "zouden",
    "kunnen", "kan", "kon", "konden", "gekund",
    "mogen", "mag", "mocht", "mochten", "gemogen",
    "moeten", "moet", "moest", "moesten", "gemoeten",
    "willen", "wil", "wilde", "wilden", "gewild"
}

# Bijwoorden (zonder betekenis)
BIJWOORDEN = {
    "niet", "wel", "ook", "nog", "al", "zeer", "heel", "erg", "nogal",
    "best", "vrij", "redelijk", "tamelijk", "behoorlijk", "enigszins",
    "zelfs", "juist", "precies", "zeker", "natuurlijk", "uiteraard",
    "misschien", "wellicht", "mogelijk", "waarschijnlijk", "eventueel"
}

# Vraagwoorden
VRAAGWOORDEN = {
    "wat", "wie", "waar", "wanneer", "waarom", "hoe", "welke", "welk",
    "hoeveel", "hoelang", "waarmee", "waardoor", "waarvan", "waarnaar"
}

# Andere functiewoorden
FUNCTIEWOORDEN = {
    "er", "zich", "daar", "hier", "dan", "toen", "nu", "straks",
    "ja", "nee", "graag", "alsjeblieft", "dank", "bedankt", "hallo", "hoi", "dag",
    "zo", "dus", "zeg", "hè", "hoor", "toch", "maar", "eens", "effe", "ff"
}

# Getallen en tijdsaanduidingen (zonder context betekenisloos)
TIJDSWOORDEN = {
    "vandaag", "gisteren", "morgen", "overmorgen", "eergisteren",
    "vandaan", "hierna", "daarna", "straks", "later", "eerder",
    "maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag",
    "januari", "februari", "maart", "april", "mei", "juni", "juli",
    "augustus", "september", "oktober", "november", "december"
}

# Combineer alle stopwords
DUTCH_STOPWORDS = (
    LIDWOORDEN | VOORZETSELS | VOEGWOORDEN | VOORNAAMWOORDEN |
    HULPWERKWOORDEN | BIJWOORDEN | VRAAGWOORDEN | FUNCTIEWOORDEN | TIJDSWOORDEN
)

# Patterns die wijzen op grammaticale woorden (niet concepten)
MEANINGLESS_PATTERNS = [
    "er zijn",
    "er is",
    "het is",
    "dat is",
    "dit is",
    "wat is",
    "wie is",
    "waar is",
    "hoe is",
    "ik ben",
    "jij bent",
    "hij is",
    "ze zijn"
]

def is_meaningful_concept(concept: str) -> tuple[bool, str]:
    """
    Check if a concept is meaningful enough to create a knowledge snap
    
    Returns:
        (is_meaningful, reason)
    """
    if not concept or not isinstance(concept, str):
        return False, "Concept is leeg"
    
    # Normalize
    concept_lower = concept.lower().strip()
    
    # 1. Length check - te kort is meestal geen concept
    if len(concept_lower) < 3:
        return False, f"Te kort ({len(concept_lower)} tekens)"
    
    # 2. Must contain letters
    if not any(c.isalpha() for c in concept_lower):
        return False, "Geen letters (alleen cijfers/symbolen)"
    
    # 3. Check if it's ONLY a stopword
    if concept_lower in DUTCH_STOPWORDS:
        return False, f"Stopword: {concept_lower}"
    
    # 4. Check if it's a meaningless pattern
    for pattern in MEANINGLESS_PATTERNS:
        if pattern in concept_lower:
            return False, f"Grammaticaal patroon: '{pattern}'"
    
    # 5. Check if it's only punctuation with one word
    words = concept_lower.split()
    if len(words) == 1 and words[0] in DUTCH_STOPWORDS:
        return False, f"Enkel stopword: {words[0]}"
    
    # 6. Check if ALL words are stopwords
    if len(words) > 1:
        meaningful_words = [w for w in words if w not in DUTCH_STOPWORDS and len(w) >= 3]
        if len(meaningful_words) == 0:
            return False, "Alleen stopwords in zin"
        
        # If less than 30% meaningful words, probably not a concept
        if len(meaningful_words) / len(words) < 0.3:
            return False, f"Te weinig betekenisvolle woorden ({len(meaningful_words)}/{len(words)})"
    
    # 7. Check for common filler phrases
    filler_phrases = [
        "o ja", "oh ja", "oke", "oké", "ok", "nou ja", "nou", "dus", "eigenlijk",
        "zeg maar", "gewoon", "eh", "uhm", "hmm", "pfff", "tja"
    ]
    if concept_lower in filler_phrases:
        return False, f"Opvulwoord: {concept_lower}"
    
    # 8. Passed all checks - it's meaningful!
    return True, "Betekenisvol concept"


def get_concept_type(concept: str) -> str:
    """
    Determine the type of concept (for logging/analytics)
    """
    concept_lower = concept.lower().strip()
    words = concept_lower.split()
    
    # Single word
    if len(words) == 1:
        if concept_lower.endswith("en"):  # Might be verb
            return "werkwoord"
        elif any(c.isupper() for c in concept):  # Contains capitals
            return "eigennaam"
        else:
            return "begrip"
    
    # Multiple words
    elif len(words) <= 3:
        return "korte_zin"
    else:
        return "lange_zin"


# For testing
if __name__ == "__main__":
    test_concepts = [
        "appel",
        "de",
        "het",
        "en",
        "klimaatverandering",
        "is",
        "wat is",
        "quantum computing",
        "er zijn",
        "fotosynthese",
        "nou ja",
        "blockchain technologie",
        "123",
        "a"
    ]
    
    print("=== STOPWORD FILTER TEST ===\n")
    for concept in test_concepts:
        is_meaningful, reason = is_meaningful_concept(concept)
        status = "✅ ACCEPT" if is_meaningful else "❌ REJECT"
        print(f"{status}: '{concept}' - {reason}")
