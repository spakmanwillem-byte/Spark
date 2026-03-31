"""
Query Priority Handler
Implementeert Willem's prioriteit systeem:

1. Mijn profiel → Welke mensen ken IK?
2. Person Cards → Mensen in mijn leven
3. Die users checken
4. Voorstellen
5. Knowledge base

Voorbeeld: "Wie is Lotus?"
→ Check Willem profiel eerst
→ Check Person Cards
→ Dan knowledge base
"""

from typing import Dict, List, Optional, Tuple
from utils.data_manager import DataManager
from services.person_card_service import PersonCardService

class QueryPriorityHandler:
    """
    Query handler met prioriteit op persoonlijk profiel
    """
    
    @staticmethod
    def search_entity_prioritized(entity: str, user_id: str, query: str = "") -> Dict:
        """
        Zoek entity met prioriteit systeem
        
        Args:
            entity: Zoekterm (bijv. "Lotus")
            user_id: Current user ID
            query: Volledige vraag (voor context)
            
        Returns:
            Best match met bron info
        """
        is_who_question = any(word in query.lower() for word in ['wie', 'who', 'persoon'])
        
        results = {
            'matches': [],
            'priority_source': None,
            'all_sources': []
        }
        
        # 1. CHECK MIJN PROFIEL (hoogste prioriteit!)
        profile_match = QueryPriorityHandler._check_user_profile(entity, user_id)
        if profile_match:
            results['matches'].append(profile_match)
            results['priority_source'] = 'user_profile'
            results['all_sources'].append('user_profile')
        
        # 2. CHECK PERSON CARDS (personen in mijn leven)
        person_matches = QueryPriorityHandler._check_person_cards(entity, user_id)
        if person_matches:
            results['matches'].extend(person_matches)
            if not results['priority_source']:
                results['priority_source'] = 'person_cards'
            results['all_sources'].append('person_cards')
        
        # 3. CHECK BEKENDE USERS (relaties)
        if is_who_question:
            user_matches = QueryPriorityHandler._check_known_users(entity, user_id)
            results['matches'].extend(user_matches)
            if user_matches:
                results['all_sources'].append('known_users')
        
        # 4. CHECK KNOWLEDGE BASE (laagste prioriteit)
        knowledge_matches = QueryPriorityHandler._check_knowledge_base(entity, is_who_question)
        results['matches'].extend(knowledge_matches)
        if knowledge_matches:
            results['all_sources'].append('knowledge_base')
        
        # Sort op priority score
        results['matches'] = sorted(
            results['matches'], 
            key=lambda x: x.get('priority_score', 0), 
            reverse=True
        )
        
        return results
    
    @staticmethod
    def _check_user_profile(entity: str, user_id: str) -> Optional[Dict]:
        """
        Check of entity in user's eigen profiel staat
        Hoogste prioriteit!
        """
        users = DataManager.load_users()
        user = next((u for u in users if u.get('id') == user_id), None)
        
        if not user:
            return None
        
        entity_lower = entity.lower()
        pers_info = user.get('persoonlijke_info', {})
        
        # Check familie relaties in persoonlijke_info
        if pers_info.get('dochter') and entity_lower in pers_info.get('dochter', '').lower():
            return {
                'type': 'person',
                'source': 'user_profile',
                'relation': 'dochter',
                'name': pers_info.get('dochter'),
                'answer': f"{pers_info.get('dochter')} is je dochter.",
                'priority_score': 100,  # Hoogste!
                'confidence': 1.0
            }
        
        if pers_info.get('partner') and entity_lower in pers_info.get('partner', '').lower():
            return {
                'type': 'person',
                'source': 'user_profile',
                'relation': 'partner',
                'name': pers_info.get('partner'),
                'answer': f"{pers_info.get('partner')} is je partner.",
                'priority_score': 100,
                'confidence': 1.0
            }
        
        # Check gamertag, hobby, etc.
        for key, value in pers_info.items():
            if isinstance(value, str) and entity_lower in value.lower():
                return {
                    'type': 'personal_info',
                    'source': 'user_profile',
                    'field': key,
                    'value': value,
                    'answer': f"In je profiel ({key}): {value}",
                    'priority_score': 95,
                    'confidence': 0.95
                }
        
        # Check andere top-level user fields
        for key, value in user.items():
            if key in ['id', 'persoonlijke_info', 'achievements', 'conversation_summaries', 'pending_agenda_items', 'profile']:
                continue  # Skip nested objects
            if isinstance(value, str) and entity_lower in value.lower():
                return {
                    'type': 'personal_info',
                    'source': 'user_profile',
                    'field': key,
                    'value': value,
                    'answer': f"In je profiel: {key} = {value}",
                    'priority_score': 90,
                    'confidence': 0.9
                }
        
        return None
    
    @staticmethod
    def _check_known_users(entity: str, user_id: str) -> List[Dict]:
        """
        Check bekende users (andere geregistreerde users)
        """
        users = DataManager.load_users()
        matches = []
        entity_lower = entity.lower()
        
        for user in users:
            if user.get('id') == user_id:
                continue  # Skip eigen profiel
            
            naam = user.get('naam', '').lower()
            volledige_naam = user.get('volledige_naam', '').lower()
            
            if entity_lower in naam or entity_lower in volledige_naam:
                matches.append({
                    'type': 'user',
                    'source': 'known_users',
                    'user_id': user.get('id'),
                    'name': user.get('naam'),
                    'full_name': user.get('volledige_naam'),
                    'gradatie': user.get('gradatie'),
                    'answer': f"{user.get('naam')} is een gebruiker (gradatie {user.get('gradatie')}).",
                    'priority_score': 80,
                    'confidence': 0.8
                })
        
        return matches
    
    @staticmethod
    def _check_person_cards(entity: str, user_id: str) -> List[Dict]:
        """
        Check Person Cards (mensen in mijn leven)
        Priority score: 90 (tussen user profile en known users)
        """
        person_cards = PersonCardService.load_person_cards(user_id)
        matches = []
        entity_lower = entity.lower()
        
        for person in person_cards:
            naam = person.get('naam', '').lower()
            volledige_naam = person.get('volledige_naam', '').lower()
            relatie = person.get('relatie', '')
            gradatie = person.get('gradatie', 5)
            
            # Match op naam
            if entity_lower in naam or entity_lower in volledige_naam:
                # Build answer
                answer_parts = [f"{person.get('naam')}"]
                
                if relatie:
                    answer_parts.append(f"is je {relatie}")
                
                if gradatie:
                    answer_parts.append(f"(gradatie {gradatie})")
                
                if person.get('notes'):
                    answer_parts.append(f"\n{person.get('notes')}")
                
                # Check conversation refs
                conv_count = len(person.get('conversation_refs', []))
                if conv_count > 0:
                    answer_parts.append(f"\n💬 {conv_count} gesprek(ken) over {person.get('naam')}")
                
                matches.append({
                    'type': 'person_card',
                    'source': 'person_cards',
                    'person_id': person.get('id'),
                    'name': person.get('naam'),
                    'full_name': person.get('volledige_naam'),
                    'relatie': relatie,
                    'gradatie': gradatie,
                    'is_user': person.get('is_user', False),
                    'tags': person.get('tags', []),
                    'conversation_count': conv_count,
                    'knowledge_count': len(person.get('knowledge_refs', [])),
                    'answer': ' '.join(answer_parts),
                    'priority_score': 90,  # High priority, below user profile
                    'confidence': 0.95
                })
        
        return matches
    
    @staticmethod
    def _check_knowledge_base(entity: str, is_who_question: bool) -> List[Dict]:
        """
        Check knowledge base (laagste prioriteit)
        """
        # Load graph nodes
        try:
            import json
            with open('/app/backend/data/graph/nodes.json', 'r') as f:
                data = json.load(f)
            nodes = data.get('nodes', [])
        except:
            return []
        
        matches = []
        entity_lower = entity.lower()
        
        for node in nodes:
            label = node.get('label', '').lower()
            content = node.get('content', '').lower()
            tags = [t.lower() for t in node.get('tags', [])]
            
            if entity_lower in label or entity_lower in ' '.join(tags):
                # Check belangrijkheid (sterren)
                belangrijkheid = node.get('metadata', {}).get('belangrijkheid', 1)
                
                # Filter voor "wie" vragen
                if is_who_question:
                    if not any(tag in tags for tag in ['naam', 'persoon', 'familie']):
                        continue  # Skip non-person kaarten
                
                # Priority score: belangrijkheid * 10 (max 30 voor 3 sterren)
                priority_score = belangrijkheid * 10
                
                matches.append({
                    'type': 'knowledge',
                    'source': 'knowledge_base',
                    'label': node.get('label'),
                    'content': node.get('content', '')[:200],
                    'belangrijkheid': belangrijkheid,
                    'gradatie': node.get('gradatie'),
                    'tags': node.get('tags', []),
                    'answer': f"{node.get('label')}: {node.get('content', '')[:150]}...",
                    'priority_score': priority_score,
                    'confidence': 0.5
                })
        
        # Sort op belangrijkheid (sterren)
        matches = sorted(matches, key=lambda x: x.get('belangrijkheid', 0), reverse=True)
        
        return matches


def handle_query_with_priority(query: str, user_id: str) -> str:
    """
    Main entry point voor query handling met prioriteit
    
    Args:
        query: User vraag (bijv. "Wie is Lotus?")
        user_id: User ID
        
    Returns:
        Antwoord string
    """
    # Extract entities (hoofdletters, maar skip vraagwoorden)
    import re
    QUESTION_WORDS = ['wie', 'wat', 'waar', 'wanneer', 'waarom', 'hoe', 'welke']
    
    entities = re.findall(r'\b([A-Z][a-z]+)\b', query)
    entities = [e for e in entities if e.lower() not in QUESTION_WORDS]
    
    if not entities:
        return None
    
    # Search eerste entity
    entity = entities[0]
    results = QueryPriorityHandler.search_entity_prioritized(entity, user_id, query)
    
    if not results['matches']:
        return None
    
    # Best match
    best = results['matches'][0]
    
    # Als meerdere matches, voorstellen
    if len(results['matches']) > 1:
        other_matches = results['matches'][1:4]  # Top 3 andere
        answer = best['answer'] + "\n\n"
        answer += "Andere betekenissen:\n"
        for match in other_matches:
            answer += f"- {match['source']}: {match.get('label', match.get('name', 'N/A'))}\n"
        return answer
    
    return best['answer']


# VOORBEELD GEBRUIK
if __name__ == "__main__":
    # Test: "Wie is Lotus?"
    query = "Wie is Lotus?"
    user_id = "user-001"
    
    result = handle_query_with_priority(query, user_id)
    print(f"Query: {query}")
    print(f"Answer: {result}")
