"""
Contextuele Emotie Tracking

Koppelt emoties aan knowledge kaarten/topics voor patroonherkenning:
- Emotie (blij, boos, bang, bedroefd)
- Topic/Knowledge kaart
- Intensiteit score
- Timestamp

Voorbeelden:
- "blij + succes + werk" (score 7.5)
- "boos + conflict + relatie" (score 9.0)
- "bang + financiën + toekomst" (score 6.0)
"""

import json
from typing import Dict, List, Optional, Tuple
from services.emotion_scorer import EmotionScorer
from utils.data_manager import DataManager
import re


class ContextualEmotionTracker:
    """Track emotions with linked topics/knowledge cards"""
    
    @staticmethod
    def extract_topics_from_text(text: str, knowledge_base: List[Dict]) -> List[Dict]:
        """
        Extract topics/knowledge cards from text
        
        Args:
            text: Input text
            knowledge_base: List of knowledge entries
            
        Returns:
            List of matched topics with relevance scores
        """
        text_lower = text.lower()
        matched_topics = []
        
        # Search for knowledge cards in text
        for entry in knowledge_base:
            begrip = entry.get('begrip', '').lower()
            tags = entry.get('tags', [])
            
            # Check if begrip is in text
            if begrip and len(begrip) > 2:  # Min 3 chars
                pattern = r'\b' + re.escape(begrip) + r'\b'
                if re.search(pattern, text_lower):
                    matched_topics.append({
                        'topic': begrip,
                        'knowledge_id': entry.get('id'),
                        'label': entry.get('begrip'),
                        'tags': tags[:3],  # Top 3 tags
                        'relevance': 0.9,  # High confidence (exact match)
                        'match_type': 'begrip'
                    })
            
            # Check tags (lower confidence)
            for tag in tags:
                if len(tag) > 3 and tag.lower() in text_lower:
                    # Avoid duplicates
                    if not any(t['topic'] == tag.lower() for t in matched_topics):
                        matched_topics.append({
                            'topic': tag.lower(),
                            'knowledge_id': entry.get('id'),
                            'label': entry.get('begrip'),
                            'tags': [tag],
                            'relevance': 0.6,  # Medium confidence (tag match)
                            'match_type': 'tag'
                        })
        
        # Sort by relevance
        matched_topics.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Return top 3 most relevant
        return matched_topics[:3]
    
    @staticmethod
    def extract_general_topics(text: str) -> List[str]:
        """
        Extract general topics using keyword extraction
        
        Fallback when no knowledge cards match
        """
        # Common topic keywords (Dutch)
        topic_keywords = {
            'werk': ['werk', 'baan', 'job', 'carrière', 'collega', 'baas', 'project'],
            'relatie': ['relatie', 'partner', 'vriend', 'vriendin', 'liefde', 'familie'],
            'gezondheid': ['gezondheid', 'ziek', 'dokter', 'ziekenhuis', 'medicijn'],
            'geld': ['geld', 'financiën', 'inkomen', 'salaris', 'budget', 'schuld'],
            'studie': ['studie', 'school', 'opleiding', 'examen', 'les', 'leren'],
            'toekomst': ['toekomst', 'doel', 'plan', 'ambitie', 'droom'],
            'verleden': ['verleden', 'vroeger', 'herinnering', 'toen'],
            'hobby': ['hobby', 'sport', 'spel', 'muziek', 'kunst'],
            'huis': ['huis', 'wonen', 'thuis', 'appartement'],
            'natuur': ['natuur', 'buiten', 'weer', 'landschap'],
        }
        
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if topic not in detected_topics:
                        detected_topics.append(topic)
                    break
        
        return detected_topics
    
    @staticmethod
    def detect_emotion_with_context(
        text: str,
        user_id: str = None
    ) -> Optional[Dict]:
        """
        Detect emotion AND linked topics/context
        
        Args:
            text: Input text
            user_id: User ID (for knowledge base access)
            
        Returns:
            {
                'emotion': 'blij',
                'word': 'gelukkig',
                'base_score': 7,
                'final_score': 12.6,
                'intensifier': 'super',
                'multiplier': 1.8,
                'context': 'super gelukkig met werk',
                'topics': [
                    {
                        'topic': 'werk',
                        'knowledge_id': 'abc123',
                        'label': 'Werk',
                        'relevance': 0.9
                    }
                ],
                'general_topics': ['werk'],
                'timestamp': '2026-03-15T18:30:00'
            }
        """
        # Detect emotion
        scorer = EmotionScorer()
        emotion_result = scorer.detect_emotion_in_text(text)
        
        if not emotion_result:
            return None
        
        # Load knowledge base
        try:
            kb_data = DataManager.load_json('learned_knowledge/knowledge_base.json')
            knowledge_base = kb_data.get('knowledge_entries', [])
        except:
            knowledge_base = []
        
        # Extract topics from knowledge base
        topics = ContextualEmotionTracker.extract_topics_from_text(text, knowledge_base)
        
        # Extract general topics (fallback)
        general_topics = ContextualEmotionTracker.extract_general_topics(text)
        
        # Combine results
        result = {
            **emotion_result,
            'topics': topics,
            'general_topics': general_topics,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        return result
    
    @staticmethod
    def format_emotion_context_summary(result: Dict) -> str:
        """
        Format emotion + context for display
        
        Args:
            result: Result from detect_emotion_with_context
            
        Returns:
            Formatted string like "blij + werk + project (score 7.5)"
        """
        emotion = result.get('emotion', 'unknown')
        score = result.get('final_score', 0)
        
        # Get topic labels
        topics = result.get('topics', [])
        general = result.get('general_topics', [])
        
        topic_labels = [t.get('topic') for t in topics]
        if not topic_labels:
            topic_labels = general[:2]  # Max 2 general topics
        
        if topic_labels:
            summary = f"{emotion} + {' + '.join(topic_labels)} (score {score})"
        else:
            summary = f"{emotion} (score {score})"
        
        return summary


def test_contextual_emotion():
    """Test contextual emotion detection"""
    tracker = ContextualEmotionTracker()
    
    test_cases = [
        "Ik ben heel blij met mijn werk vandaag",
        "Ik ben super boos over het conflict met mijn collega",
        "Ik ben een beetje bang voor de toekomst en financiën",
        "Ik voel me verdrietig over mijn relatie",
        "Extreem gelukkig met mijn project succes!",
    ]
    
    print("=" * 80)
    print("CONTEXTUELE EMOTIE DETECTIE TEST")
    print("=" * 80)
    
    for text in test_cases:
        print(f"\n📝 Text: '{text}'")
        result = tracker.detect_emotion_with_context(text)
        
        if result:
            print(f"   Emotie: {result['emotion']} (score: {result['final_score']})")
            
            if result.get('intensifier'):
                print(f"   Versterker: {result['intensifier']} (×{result['multiplier']})")
            
            if result.get('topics'):
                print(f"   📚 Gekoppelde Knowledge:")
                for topic in result['topics']:
                    print(f"      - {topic['topic']} ({topic['label']}) [relevance: {topic['relevance']}]")
            
            if result.get('general_topics'):
                print(f"   🏷️  Algemene Topics: {', '.join(result['general_topics'])}")
            
            # Format summary
            summary = tracker.format_emotion_context_summary(result)
            print(f"   📊 Summary: {summary}")
        else:
            print("   ❌ Geen emotie gedetecteerd")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_contextual_emotion()
