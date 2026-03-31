"""
Query Handler met Gradatie Ranking
Gebruikt Willem's gradatie systeem voor disambiguation
"""

def handle_query_with_gradatie_rank(query, user_data):
    """
    Beantwoord query met gradatie-based ranking
    
    Gradatie 1 (familie/persoon) > Gradatie 4 (algemene kennis)
    
    Args:
        query: User vraag
        user_data: User profile (voor persoonlijke context)
    
    Returns:
        Best match op basis van gradatie
    """
    
    # 1. Extract entities uit query
    entities = extract_entities(query)  # bijv. ["Lotus"]
    
    # 2. Check of het een "WIE" vraag is
    is_who_question = any(word in query.lower() for word in ['wie', 'who', 'persoon'])
    
    # 3. Search in graph
    from services.graph_service import GraphService
    all_matches = []
    
    for entity in entities:
        # Search in knowledge graph
        results = GraphService.search_nodes(entity)
        all_matches.extend(results)
    
    # 4. RANK op gradatie (Willem's systeem!)
    ranked = sorted(all_matches, key=lambda x: x.get('gradatie', 999))
    
    # 5. Filter op type als "WIE" vraag
    if is_who_question:
        # Filter alleen personen (gradatie 1-2 + familie tags)
        personen = [
            r for r in ranked 
            if r.get('gradatie') in [1, 2] or 
            any(tag in ['familie', 'dochter', 'persoon'] for tag in r.get('tags', []))
        ]
        
        if personen:
            ranked = personen
    
    # 6. Return best match
    if ranked:
        best = ranked[0]
        
        # Check relatie met user
        if best.get('gradatie') == 1:
            # Familie/persoonlijk
            tags = best.get('tags', [])
            if 'dochter' in tags:
                relatie = "je dochter"
            elif 'partner' in tags:
                relatie = "je partner"
            elif 'familie' in tags:
                relatie = "familie van je"
            else:
                relatie = "persoonlijk belangrijk voor je"
            
            return {
                'answer': f"{best.get('label')} is {relatie}. (Gradatie 1 - hoogste vertrouwen)",
                'source': 'persoonlijk',
                'gradatie': 1,
                'all_matches': len(ranked)
            }
        else:
            # Algemene kennis
            return {
                'answer': f"{best.get('label')}: {best.get('content', 'Geen info beschikbaar.')[:200]}",
                'source': 'knowledge_base',
                'gradatie': best.get('gradatie'),
                'all_matches': len(ranked)
            }
    
    return None


def extract_entities(query):
    """
    Extract hoofdwoorden uit query
    Simpel: Hoofdletters of bekende namen
    """
    import re
    
    # Find capitalized words (likely entities)
    entities = re.findall(r'\b([A-Z][a-z]+)\b', query)
    
    # Also check lowercase for known names
    known_names = ['lotus', 'willem', 'spark', 'roadkill']
    for name in known_names:
        if name in query.lower():
            entities.append(name.capitalize())
    
    return list(set(entities))


# VOORBEELD GEBRUIK:
"""
Query: "Wie is Lotus?"

1. Extract: ["Lotus"]
2. is_who_question: True (heeft "wie")
3. Search: 4 matches gevonden
   - Lotus dochter (gradatie 1, tags: familie, dochter)
   - Lotus koekje (gradatie 4)
   - Lotusbloem (gradatie 4)
   - Lotus auto (gradatie 4)

4. Rank op gradatie:
   [1] Lotus dochter (gradatie 1)
   [2] Lotus koekje (gradatie 4)
   [3] Lotusbloem (gradatie 4)
   [4] Lotus auto (gradatie 4)

5. Filter op "WIE":
   → Alleen Lotus dochter (heeft 'familie' tag)

6. Return:
   "Lotus Spakman is je dochter. (Gradatie 1 - hoogste vertrouwen)"
"""
