"""
Emotie Scoring Systeem

Combineert basis intensiteit scores met context versterkers:
- Basis: blij=5, gelukkig=7, euforisch=10
- Versterkers: "heel" (1.5x), "erg" (1.5x), "super" (1.8x), "extreem" (2.0x)
- Verzwakkers: "een beetje" (0.5x), "iets" (0.7x)

Voorbeeld:
- "blij" = 5
- "heel blij" = 5 × 1.5 = 7.5
- "extreem boos" = 5 × 2.0 = 10
"""

import json
import re
from typing import Dict, Tuple, Optional


# Emotie intensiteit scores (basis)
EMOTION_SCORES = {
    'blij': {
        'blij': 5,
        'gelukkig': 7,
        'vrolijk': 6,
        'tevreden': 4,
        'opgetogen': 8,
        'euforisch': 10,
        'verheugd': 6,
        'enthousiast': 7,
        'dankbaar': 5,
        'opgewekt': 5,
        'fijn': 4,
        'goed': 3,
        'prettig': 4,
        'feest': 7,
        'geweldig': 8,
        'fantastisch': 9,
        'perfect': 9,
    },
    'boos': {
        'boos': 5,
        'woedend': 10,
        'kwaad': 6,
        'geïrriteerd': 3,
        'gefrustreerd': 4,
        'teleurgesteld': 4,
        'verbolgen': 7,
        'razend': 9,
        'gepikeerd': 3,
        'geërgerd': 3,
        'furieus': 9,
        'agressief': 8,
    },
    'bang': {
        'bang': 5,
        'angstig': 6,
        'nerveus': 3,
        'bezorgd': 4,
        'ongerust': 4,
        'doodsbang': 10,
        'paniekerig': 9,
        'gespannen': 4,
        'onzeker': 3,
        'schrikken': 7,
        'angst': 6,
        'vrees': 5,
    },
    'bedroefd': {
        'bedroefd': 5,
        'verdrietig': 7,
        'somber': 6,
        'depressief': 10,
        'down': 5,
        'neerslachtig': 7,
        'melancholisch': 6,
        'triest': 6,
        'ellendig': 8,
        'zwaarmoedig': 7,
        'droef': 5,
        'huilen': 7,
        'verdriet': 7,
    }
}

# Context versterkers (multipliers)
INTENSIFIERS = {
    # Sterke versterkers (>1.5x)
    'extreem': 2.0,
    'enorm': 2.0,
    'verschrikkelijk': 2.0,
    'vreselijk': 2.0,
    'ontzettend': 1.8,
    'super': 1.8,
    'mega': 1.8,
    'ultiem': 2.0,
    
    # Medium versterkers (1.3-1.5x)
    'heel': 1.5,
    'erg': 1.5,
    'zeer': 1.5,
    'zo': 1.3,
    'best': 1.3,
    'behoorlijk': 1.4,
    'redelijk': 1.2,
    
    # Verzwakkers (<1.0x)
    'een beetje': 0.5,
    'beetje': 0.6,
    'iets': 0.7,
    'licht': 0.7,
    'enigszins': 0.8,
    'tamelijk': 0.9,
    'vrij': 0.9,
}


class EmotionScorer:
    """Calculate emotion scores with intensity and context"""
    
    @staticmethod
    def detect_emotion_in_text(text: str) -> Optional[Dict]:
        """
        Detect emotion and calculate score from text
        
        Handles negations like "niet goed", "niet blij"
        
        Returns:
            {
                'emotion': 'blij',
                'word': 'gelukkig',
                'base_score': 7,
                'intensifier': 'heel',
                'multiplier': 1.5,
                'final_score': 10.5,
                'context': 'heel gelukkig'
            }
            or None if no emotion detected
        """
        text_lower = text.lower()
        
        # Check for questions about Spark's emotions (not user's emotions!)
        # "ben jij blij", "ben jij bang" → skip these
        if re.search(r'\b(ben jij|ben je|voel jij|voel je)\b', text_lower):
            return None
        
        # Search for emotions
        for emotion_type, words_dict in EMOTION_SCORES.items():
            for word, base_score in words_dict.items():
                # Find word in text (word boundary check)
                pattern = r'\b' + re.escape(word) + r'\b'
                match = re.search(pattern, text_lower)
                
                if match:
                    # Check for negation words BEFORE the emotion
                    # "niet goed", "geen goed", "nooit goed"
                    start_pos = max(0, match.start() - 50)  # Look 50 chars back
                    context = text_lower[start_pos:match.end()]
                    
                    # Check for negation (skip if negated)
                    negation_words = ['niet', 'geen', 'nooit', 'nergens', 'niemand']
                    is_negated = False
                    for neg_word in negation_words:
                        if neg_word in context:
                            # Check if negation is within 3 words of emotion
                            neg_pos = context.rfind(neg_word)
                            word_distance = len(context[neg_pos:match.start()].split())
                            if word_distance <= 3:
                                is_negated = True
                                break
                    
                    # Skip negated emotions (they're not expressing this emotion)
                    if is_negated:
                        continue
                    
                    # Find intensifier
                    intensifier = None
                    multiplier = 1.0
                    
                    for intens_word, intens_mult in INTENSIFIERS.items():
                        if intens_word in context:
                            # Check if intensifier is within 3 words of emotion word
                            intens_pos = context.rfind(intens_word)
                            word_distance = len(context[intens_pos:match.start()].split())
                            
                            if word_distance <= 3:
                                intensifier = intens_word
                                multiplier = intens_mult
                                break  # Use first found intensifier
                    
                    final_score = round(base_score * multiplier, 1)
                    
                    return {
                        'emotion': emotion_type,
                        'word': word,
                        'base_score': base_score,
                        'intensifier': intensifier,
                        'multiplier': multiplier,
                        'final_score': final_score,
                        'context': context.strip()
                    }
        
        return None
    
    @staticmethod
    def get_emotion_color(emotion: str) -> str:
        """Get color for emotion visualization"""
        colors = {
            'blij': '#4CAF50',  # Green
            'boos': '#F44336',  # Red
            'bang': '#FF9800',  # Orange
            'bedroefd': '#2196F3'  # Blue
        }
        return colors.get(emotion, '#9E9E9E')
    
    @staticmethod
    def get_intensity_level(score: float) -> str:
        """Get intensity level description"""
        if score <= 3:
            return 'Laag'
        elif score <= 6:
            return 'Medium'
        elif score <= 8:
            return 'Hoog'
        else:
            return 'Zeer Hoog'


def update_emotion_triggers_with_scores():
    """Update emotion_triggers.json with scores"""
    trigger_file = '/app/backend/data/triggers/emotion_triggers.json'
    
    with open(trigger_file, 'r') as f:
        data = json.load(f)
    
    # Update triggers with scores
    for emotion_type, words_dict in EMOTION_SCORES.items():
        if emotion_type in data['emotions']:
            data['emotions'][emotion_type]['triggers'] = words_dict
            data['emotions'][emotion_type]['description'] = f"Emotie woorden voor {emotion_type} met intensiteit scores (1-10)"
    
    # Add intensifiers info
    data['metadata']['intensifiers'] = INTENSIFIERS
    data['metadata']['scoring_system'] = {
        'type': 'intensity_with_context',
        'description': 'Basis intensiteit scores (1-10) × context versterkers',
        'example': 'heel blij = 5 × 1.5 = 7.5'
    }
    
    with open(trigger_file, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Updated {trigger_file} with scores")


if __name__ == "__main__":
    # Test
    scorer = EmotionScorer()
    
    test_texts = [
        "Ik ben blij",
        "Ik ben heel blij",
        "Ik ben super gelukkig",
        "Ik ben extreem boos",
        "Ik ben een beetje bang",
        "Ik voel me ontzettend verdrietig"
    ]
    
    print("=" * 60)
    print("EMOTIE SCORING TEST")
    print("=" * 60)
    
    for text in test_texts:
        result = scorer.detect_emotion_in_text(text)
        if result:
            print(f"\n📝 '{text}'")
            print(f"   Emotie: {result['emotion']}")
            print(f"   Woord: {result['word']} (basis: {result['base_score']})")
            if result['intensifier']:
                print(f"   Versterker: {result['intensifier']} (×{result['multiplier']})")
            print(f"   🎯 Score: {result['final_score']} ({scorer.get_intensity_level(result['final_score'])})")
    
    print("\n" + "=" * 60)
    print("Updating emotion_triggers.json...")
    update_emotion_triggers_with_scores()
