"""
Spark Response Generator - Emotion + Core Principles Integration
Combineert emotie engine met normen, waarden, en bijbelkaarten voor contextuele reacties
"""
from typing import Dict, List, Optional
from services.emotion_service import EmotionService
from utils.data_manager import DataManager
import random


class SparkResponseGenerator:
    """
    Genereert Spark reacties gebaseerd op:
    1. Emotie state (toon, max words)
    2. Normen & Waarden (principes)
    3. Bijbelkaarten (levenswijs)
    4. Knowledge base (feiten)
    """
    
    @staticmethod
    def generate_response(
        query: str,
        context: Optional[Dict] = None,
        emotion_override: Optional[str] = None
    ) -> Dict:
        """
        Genereer response gebaseerd op emotie + core principes
        
        Args:
            query: De vraag/input van Willem
            context: Extra context (situatie, tags, etc.)
            emotion_override: Force specifieke emotie (voor testing)
        
        Returns:
            {
                "response": "De reactie tekst",
                "emotion": {"state": "happy", "sub_state": "vreugde"},
                "tone": "positive",
                "max_words": 250,
                "applied_principles": ["Autonomie", "Fundament eerst"],
                "reasoning": "Waarom deze reactie"
            }
        """
        # 1. GET CURRENT EMOTION
        if emotion_override:
            emotion_data = SparkResponseGenerator._get_emotion_config(emotion_override)
        else:
            current = EmotionService.get_current_emotion()
            emotion_data = SparkResponseGenerator._get_emotion_config(
                current.get('state', 'neutral'),
                current.get('sub_state')
            )
        
        # 2. CHECK RELEVANT PRINCIPLES (normen, waarden, bijbel)
        relevant_principles = SparkResponseGenerator._find_relevant_principles(
            query, 
            context
        )
        
        # 3. GENERATE BASE RESPONSE
        response_parts = []
        
        # Add emotion-based opening
        if emotion_data.get('examples'):
            opening = random.choice(emotion_data['examples'])
            response_parts.append(opening)
        
        # Add principle-based guidance
        if relevant_principles:
            principle_text = SparkResponseGenerator._apply_principles(
                query,
                relevant_principles,
                emotion_data
            )
            response_parts.append(principle_text)
        
        # 4. COMBINE & LIMIT
        full_response = " ".join(response_parts)
        max_words = emotion_data.get('max_words', 150)
        
        # Truncate if needed
        words = full_response.split()
        if len(words) > max_words:
            full_response = " ".join(words[:max_words]) + "..."
        
        # 5. RETURN STRUCTURED RESPONSE
        return {
            "response": full_response,
            "emotion": {
                "state": emotion_data.get('state', 'neutral'),
                "sub_state": emotion_data.get('sub_state'),
                "tone": emotion_data.get('tone', 'neutral')
            },
            "max_words": max_words,
            "applied_principles": [p['name'] for p in relevant_principles],
            "reasoning": SparkResponseGenerator._explain_reasoning(
                relevant_principles,
                emotion_data
            ),
            "word_count": len(full_response.split())
        }
    
    @staticmethod
    def _get_emotion_config(state: str, sub_state: Optional[str] = None) -> Dict:
        """Get emotion configuration from spark_emotions.json"""
        all_emotions = EmotionService.get_all_emotions()
        
        emotion = all_emotions.get(state, all_emotions.get('neutral'))
        
        result = {
            "state": state,
            "tone": emotion.get('tone', 'neutral'),
            "examples": emotion.get('examples', [])
        }
        
        # If sub_emotion specified
        if sub_state and 'sub_emotions' in emotion:
            sub_emotion = emotion['sub_emotions'].get(sub_state, {})
            result.update({
                "sub_state": sub_state,
                "max_words": sub_emotion.get('max_words', 150),
                "examples": sub_emotion.get('examples', result['examples']),
                "linked_mode": sub_emotion.get('linked_mode', 'neutral_mode')
            })
        else:
            result['max_words'] = emotion.get('max_words', 150)
            result['sub_state'] = None
        
        return result
    
    @staticmethod
    def _find_relevant_principles(query: str, context: Optional[Dict]) -> List[Dict]:
        """
        Zoek relevante normen, waarden, en bijbelkaarten op basis van:
        - Query keywords
        - Context tags
        - WS5 matching
        """
        bijbel = DataManager.load_json("personality/spark_bijbel.json")
        
        relevant = []
        query_lower = query.lower()
        context_tags = context.get('tags', []) if context else []
        
        # Check normen
        for norm in bijbel.get('normen', []):
            score = SparkResponseGenerator._calculate_relevance(
                query_lower,
                norm,
                context_tags
            )
            if score > 0.3:
                relevant.append({
                    "type": "norm",
                    "name": norm['norm'],
                    "content": norm,
                    "score": score
                })
        
        # Check waarden
        for waarde in bijbel.get('kernwaarden', []):
            score = SparkResponseGenerator._calculate_relevance(
                query_lower,
                waarde,
                context_tags
            )
            if score > 0.3:
                relevant.append({
                    "type": "waarde",
                    "name": waarde['waarde'],
                    "content": waarde,
                    "score": score
                })
        
        # Check bijbelkaarten (highest priority!)
        for bijbel_item in bijbel.get('bijbel_items', []):
            score = SparkResponseGenerator._calculate_relevance(
                query_lower,
                bijbel_item,
                context_tags
            )
            if score > 0.3:
                relevant.append({
                    "type": "bijbel",
                    "name": bijbel_item['naam'],
                    "content": bijbel_item,
                    "score": score
                })
        
        # Sort by score (bijbel heeft voorkeur bij gelijke score)
        relevant.sort(key=lambda x: (x['score'], 1 if x['type'] == 'bijbel' else 0), reverse=True)
        
        # Return top 3
        return relevant[:3]
    
    @staticmethod
    def _calculate_relevance(query: str, item: Dict, context_tags: List[str]) -> float:
        """
        Calculate relevance score (0-1) based on:
        - Tag matches
        - Keyword matches in naam/beschrijving
        - WS5 matches
        """
        score = 0.0
        
        # Tag matching (strongest signal)
        item_tags = item.get('tags', [])
        matching_tags = set(item_tags) & set(context_tags)
        if item_tags:
            score += (len(matching_tags) / len(item_tags)) * 0.5
        
        # Keyword matching in naam/norm/waarde
        name_field = item.get('naam') or item.get('norm') or item.get('waarde', '')
        if name_field and any(word in query for word in name_field.lower().split()):
            score += 0.3
        
        # Description matching
        beschrijving = item.get('beschrijving', '')
        if beschrijving and any(word in query for word in beschrijving.lower().split()[:20]):
            score += 0.2
        
        # WS5 matching (especially "why" and "how")
        ws5 = item.get('ws5', {})
        if ws5:
            why_match = any(word in query for word in ws5.get('why', '').lower().split()[:10])
            how_match = any(word in query for word in ws5.get('how', '').lower().split()[:10])
            if why_match or how_match:
                score += 0.2
        
        return min(score, 1.0)
    
    @staticmethod
    def _apply_principles(query: str, principles: List[Dict], emotion: Dict) -> str:
        """
        Generate principle-based response text
        """
        if not principles:
            return ""
        
        # Use top principle
        top = principles[0]
        content = top['content']
        
        # Extract wisdom
        if top['type'] == 'bijbel':
            # Bijbelkaart - use situation wisdom
            desc = content['beschrijving']
            # Take first meaningful sentence
            sentences = desc.split('.')
            wisdom = sentences[0] + '.' if sentences else desc[:100]
            
            return f"Dit doet me denken aan: {wisdom}"
        
        elif top['type'] == 'norm':
            # Norm - use core principle
            norm_name = content['norm']
            why = content.get('ws5', {}).get('why', content['beschrijving'])
            
            return f"Volgens '{norm_name}': {why[:100]}"
        
        elif top['type'] == 'waarde':
            # Waarde - use core value
            waarde_name = content['waarde']
            why = content.get('ws5', {}).get('why', content['beschrijving'])
            
            return f"Onze waarde '{waarde_name}' zegt: {why[:100]}"
        
        return ""
    
    @staticmethod
    def _explain_reasoning(principles: List[Dict], emotion: Dict) -> str:
        """Generate explanation of why this response was given"""
        parts = []
        
        # Emotion reasoning
        emotion_state = emotion.get('state', 'neutral')
        tone = emotion.get('tone', 'neutral')
        parts.append(f"Emotie: {emotion_state} ({tone} toon)")
        
        # Principle reasoning
        if principles:
            principle_names = [p['name'] for p in principles]
            parts.append(f"Principes: {', '.join(principle_names)}")
        else:
            parts.append("Geen specifieke principes getriggerd")
        
        return " | ".join(parts)


# USAGE EXAMPLES:
"""
# Example 1: Question about speed vs quality
response = SparkResponseGenerator.generate_response(
    query="Moet ik deze feature snel maken?",
    context={"tags": ["groei", "fundament", "ontwikkeling"]},
    emotion_override="happy"  # or None for current emotion
)

# Output:
{
    "response": "Wat fijn om te horen! Volgens 'Fundament vóór uitbreiding': Stabiliteit > snelheid. Check eerst of fundament stabiel is.",
    "emotion": {"state": "happy", "sub_state": "blijdschap", "tone": "positive"},
    "max_words": 150,
    "applied_principles": ["Fundament vóór uitbreiding", "Rust boven snelheid"],
    "reasoning": "Emotie: happy (positive toon) | Principes: Fundament vóór uitbreiding, Rust boven snelheid"
}


# Example 2: Confusion about AI behavior
response = SparkResponseGenerator.generate_response(
    query="Mag AI dit automatisch doen?",
    context={"tags": ["ai", "autonomie", "controle"]}
)

# Output:
{
    "response": "Laten we samen kijken naar een oplossing. Onze waarde 'Autonomie' zegt: Mens blijft eigenaar. AI ondersteunt, mens beslist.",
    "emotion": {"state": "neutral", "tone": "neutral"},
    "applied_principles": ["Autonomie", "AI ondersteunt, mens beslist"],
    ...
}


# Example 3: Stressful situation (emotion affects tone!)
EmotionService.set_emotion("angry", "irritatie")

response = SparkResponseGenerator.generate_response(
    query="Deze bug is frustrerend!",
    context={"tags": ["fundament", "stabiliteit"]}
)

# Output:
{
    "response": "Ik begrijp dat dit lastig is, maar laten we een oplossing vinden. Volgens 'Fundament vóór uitbreiding': Check stabiliteit eerst.",
    "emotion": {"state": "angry", "sub_state": "irritatie", "tone": "serious"},
    "max_words": 250,
    ...
}
"""
