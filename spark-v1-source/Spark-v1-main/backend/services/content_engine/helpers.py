"""
Helper functies voor Content Engine modules
"""
import re
from typing import List, Tuple


def count_words(text: str) -> int:
    """Tel aantal woorden"""
    return len(text.split())


def calculate_avg_word_length(text: str) -> float:
    """Bereken gemiddelde woordlengte"""
    words = text.split()
    if not words:
        return 0.0
    return sum(len(word) for word in words) / len(words)


def count_questions(text: str) -> int:
    """Tel aantal vragen (zinnen met ?)"""
    return text.count('?')


def has_emoji(text: str) -> bool:
    """Detecteer emoji's (basic check)"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "]+",
        flags=re.UNICODE
    )
    return bool(emoji_pattern.search(text))


def has_capitals_emphasis(text: str) -> bool:
    """Detecteer nadruk via hoofdletters (bijv. WAAROM)"""
    words = text.split()
    # Check if any word (>2 chars) is all caps
    return any(word.isupper() and len(word) > 2 for word in words)


def has_punctuation_emphasis(text: str) -> bool:
    """Detecteer nadruk via meerdere leestekens (!!! of ???)"""
    return bool(re.search(r'[!?]{2,}', text))


def calculate_formality(text: str) -> float:
    """
    Bereken formaliteit (0.0 = casual, 1.0 = formal)
    
    Indicators:
    - Gebruik van u/jij
    - Lengte zinnen
    - Gebruik van emoji/slang
    - Punctuatie
    """
    score = 0.5  # Start neutral
    text_lower = text.lower()
    
    # Formal markers (+)
    if ' u ' in f' {text_lower} ':  # "u" als aanspreekvorm
        score += 0.3
    if any(word in text_lower for word in ['alstublieft', 'meneer', 'mevrouw']):
        score += 0.2
    if count_words(text) > 20:  # Langere zinnen = formeler
        score += 0.1
    
    # Casual markers (-)
    if any(word in text_lower for word in ['hey', 'hoi', 'yo', 'haha', 'lol']):
        score -= 0.2
    if has_emoji(text):
        score -= 0.2
    if has_punctuation_emphasis(text):
        score -= 0.1
    
    # Clamp between 0 and 1
    return max(0.0, min(1.0, score))


def detect_question_type(text: str) -> str:
    """
    Detecteer type vraag
    Returns: "what", "how", "why", "who", "when", "where", "yes_no", "unknown"
    """
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['wat', 'welke', 'welk']):
        return 'what'
    elif any(word in text_lower for word in ['hoe', 'hoeveel']):
        return 'how'
    elif 'waarom' in text_lower:
        return 'why'
    elif any(word in text_lower for word in ['wie', 'wiens']):
        return 'who'
    elif 'wanneer' in text_lower:
        return 'when'
    elif 'waar' in text_lower:
        return 'where'
    elif '?' in text and not any(w in text_lower for w in ['wat', 'wie', 'waar', 'wanneer', 'waarom', 'hoe']):
        return 'yes_no'
    else:
        return 'unknown'


def extract_keywords(text: str, limit: int = 5) -> List[str]:
    """
    Extracteer top keywords (simple frequency-based)
    Filtert stopwoorden en korte woorden
    """
    # Nederlandse stopwoorden (basis set)
    stopwords = {
        'de', 'het', 'een', 'en', 'van', 'in', 'is', 'dat', 'op', 'te', 'voor',
        'met', 'zijn', 'je', 'aan', 'er', 'ook', 'dit', 'om', 'kan', 'maar',
        'bij', 'wat', 'mijn', 'hij', 'niet', 'ze', 'wordt', 'hebben', 'als',
        'zijn', 'was', 'of', 'heeft', 'naar', 'dan', 'geen', 'meer', 'zou',
        'ik', 'me', 'jij', 'jou', 'we', 'ons'
    }
    
    # Clean en split
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter stopwoorden
    keywords = [w for w in words if w not in stopwords]
    
    # Count frequencies
    from collections import Counter
    word_freq = Counter(keywords)
    
    # Return top N
    return [word for word, _ in word_freq.most_common(limit)]


def calculate_emotional_intensity(text: str, sentiment: str) -> float:
    """
    Bereken emotionele intensiteit (0.0 = vlak, 1.0 = intens)
    
    Gebaseerd op:
    - Hoofdletters
    - Leestekens
    - Emotionele woorden
    - Lengte bericht
    """
    intensity = 0.0
    
    # Hoofdletters nadruk
    if has_capitals_emphasis(text):
        intensity += 0.3
    
    # Leestekens nadruk
    if has_punctuation_emphasis(text):
        intensity += 0.3
    
    # Emoji (emotioneel)
    if has_emoji(text):
        intensity += 0.2
    
    # Sentiment boost
    if sentiment in ['positief', 'negatief']:
        intensity += 0.2
    
    return min(1.0, intensity)
