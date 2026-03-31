"""
Emotion Statistics Storage & API

Stores emotion scores over time for statistics and graphs
"""

import json
from datetime import datetime
from typing import List, Dict
import os


class EmotionStats:
    """Store and retrieve emotion statistics"""
    
    STATS_DIR = "/app/backend/data/emotions"
    
    @staticmethod
    def _ensure_dir():
        """Ensure emotions directory exists"""
        os.makedirs(EmotionStats.STATS_DIR, exist_ok=True)
    
    @staticmethod
    def _get_stats_file(user_id: str) -> str:
        """Get emotion stats file for user"""
        EmotionStats._ensure_dir()
        return os.path.join(EmotionStats.STATS_DIR, f"{user_id}_emotion_history.json")
    
    @staticmethod
    def add_emotion_event(
        user_id: str,
        emotion: str,
        word: str,
        base_score: float,
        final_score: float,
        intensifier: str = None,
        multiplier: float = 1.0,
        context: str = None,
        topics: List[Dict] = None,
        general_topics: List[str] = None
    ):
        """
        Add an emotion event to history
        
        Args:
            user_id: User ID
            emotion: Emotion type (blij, boos, bang, bedroefd)
            word: Detected word
            base_score: Base intensity score
            final_score: Final score after multiplier
            intensifier: Context intensifier word (optional)
            multiplier: Multiplier applied
            context: Text context
            topics: Linked knowledge card topics (optional)
            general_topics: General topic keywords (optional)
        """
        filepath = EmotionStats._get_stats_file(user_id)
        
        # Load existing
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
        else:
            data = {
                'events': [],
                'summary': {
                    'total_events': 0,
                    'emotions': {
                        'blij': 0,
                        'boos': 0,
                        'bang': 0,
                        'bedroefd': 0
                    }
                }
            }
        
        # Add event
        event = {
            'timestamp': datetime.now().isoformat(),
            'emotion': emotion,
            'word': word,
            'base_score': base_score,
            'final_score': final_score,
            'intensifier': intensifier,
            'multiplier': multiplier,
            'context': context,
            'topics': topics or [],
            'general_topics': general_topics or []
        }
        
        data['events'].append(event)
        
        # Update summary
        data['summary']['total_events'] += 1
        data['summary']['emotions'][emotion] += 1
        data['summary']['last_updated'] = datetime.now().isoformat()
        
        # Save
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def get_emotion_history(user_id: str, limit: int = 100) -> List[Dict]:
        """Get recent emotion events"""
        filepath = EmotionStats._get_stats_file(user_id)
        
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        events = data.get('events', [])
        return events[-limit:]  # Most recent
    
    @staticmethod
    def get_emotion_summary(user_id: str) -> Dict:
        """Get emotion summary statistics"""
        filepath = EmotionStats._get_stats_file(user_id)
        
        if not os.path.exists(filepath):
            return {
                'total_events': 0,
                'emotions': {'blij': 0, 'boos': 0, 'bang': 0, 'bedroefd': 0}
            }
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return data.get('summary', {})
    
    @staticmethod
    def get_average_scores(user_id: str) -> Dict:
        """Get average emotion scores"""
        events = EmotionStats.get_emotion_history(user_id, limit=1000)
        
        if not events:
            return {}
        
        # Calculate averages per emotion
        emotion_scores = {
            'blij': [],
            'boos': [],
            'bang': [],
            'bedroefd': []
        }
        
        for event in events:
            emotion = event.get('emotion')
            score = event.get('final_score')
            if emotion and score:
                emotion_scores[emotion].append(score)
        
        averages = {}
        for emotion, scores in emotion_scores.items():
            if scores:
                averages[emotion] = {
                    'average': round(sum(scores) / len(scores), 1),
                    'count': len(scores),
                    'min': min(scores),
                    'max': max(scores)
                }
        
        return averages
