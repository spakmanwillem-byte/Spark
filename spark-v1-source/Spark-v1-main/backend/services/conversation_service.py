from typing import Dict, List, Optional
from datetime import datetime
from utils.data_manager import DataManager
from services.entity_service import EntityService
from services.classification_service import ClassificationService
from services.nlp_service import NLPService
from services.feedback_service import FeedbackService
import uuid

class ConversationService:
    def __init__(self):
        self.entity_service = EntityService()
        self.classification_service = ClassificationService()
        self.nlp_service = NLPService()
    
    def log_conversation(self, user_id: str, message: str, response: str, user_data: Optional[Dict] = None):
        """
        Log a conversation with full analysis
        """
        # Create conversation entry
        conversation_id = f"conv-{str(uuid.uuid4())[:8]}"
        timestamp = datetime.utcnow().isoformat()
        
        # Analyze user message
        user_analysis = self._analyze_message(message, user_data)
        
        # Create conversation record
        conversation = {
            "id": conversation_id,
            "timestamp": timestamp,
            "user_id": user_id,
            "user_message": message,
            "spark_response": response,
            "analysis": user_analysis,
            "metadata": {
                "user_naam": user_data.get("naam") if user_data else "Unknown",
                "gesprek_nummer": self._get_conversation_count(user_id) + 1
            }
        }
        
        # Save to user's conversation log
        self._save_conversation(user_id, conversation)
        
        # Check if response is poor and log feedback
        if FeedbackService.detect_poor_response(response):
            FeedbackService.log_feedback(
                user_id=user_id,
                user_naam=user_data.get("naam") if user_data else "Unknown",
                question=message,
                spark_answer=response,
                conversation_id=conversation_id,
                status="poor"
            )
        
        # Update analytics
        self._update_analytics(user_id, user_analysis)
        
        return conversation
    
    def _analyze_message(self, text: str, user_data: Optional[Dict] = None) -> Dict:
        """
        Comprehensive analysis of message
        """
        # Extract entities
        entities = self.entity_service.extract_entities(text)
        
        # Extract relationships
        relationships = self.entity_service.extract_relationships(text, entities)
        
        # Classify topic
        classification = self.classification_service.classify_topic(text, entities)
        
        # Detect sentiment
        sentiment = self.nlp_service.detect_sentiment(text)
        
        # Detect if question
        is_question = self.nlp_service.is_question(text)
        
        # Detect command
        command = self.nlp_service.detect_command(text)
        
        return {
            "entities": entities,
            "relationships": relationships,
            "classification": classification,
            "sentiment": sentiment,
            "is_question": is_question,
            "command": command[0] if command else None,
            "word_count": len(text.split()),
            "has_entities": bool(entities.get("personen") or entities.get("locaties"))
        }
    
    def _save_conversation(self, user_id: str, conversation: Dict):
        """Save conversation to user's log file"""
        filename = f"conversations/{user_id}_conversations.json"
        
        # Load existing conversations
        try:
            data = DataManager.load_json(filename)
            conversations = data.get("conversations", [])
        except:
            conversations = []
        
        # Add new conversation
        conversations.append(conversation)
        
        # Keep last 1000 conversations
        if len(conversations) > 1000:
            conversations = conversations[-1000:]
        
        # Save
        data = {
            "user_id": user_id,
            "total_conversations": len(conversations),
            "conversations": conversations,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        DataManager.save_json(filename, data)
    
    def _get_conversation_count(self, user_id: str) -> int:
        """Get number of conversations for user"""
        filename = f"conversations/{user_id}_conversations.json"
        try:
            data = DataManager.load_json(filename)
            return data.get("total_conversations", 0)
        except:
            return 0
    
    def _update_analytics(self, user_id: str, analysis: Dict):
        """Update user analytics based on conversation"""
        filename = f"analytics/{user_id}_analytics.json"
        
        # Load existing analytics
        try:
            analytics = DataManager.load_json(filename)
        except:
            analytics = {
                "user_id": user_id,
                "total_messages": 0,
                "topics": {},
                "entities_mentioned": {},
                "sentiment_history": [],
                "interests": {},
                "patterns": {}
            }
        
        # Update counts
        analytics["total_messages"] = analytics.get("total_messages", 0) + 1
        
        # Track topics
        klasse = analysis["classification"]["klasse"]
        if "topics" not in analytics:
            analytics["topics"] = {}
        analytics["topics"][klasse] = analytics["topics"].get(klasse, 0) + 1
        
        # Track entities
        if "entities_mentioned" not in analytics:
            analytics["entities_mentioned"] = {}
        
        for entity_type, entity_list in analysis["entities"].items():
            if entity_list:
                for entity in entity_list:
                    key = f"{entity_type}:{entity}"
                    analytics["entities_mentioned"][key] = analytics["entities_mentioned"].get(key, 0) + 1
        
        # Track sentiment
        if "sentiment_history" not in analytics:
            analytics["sentiment_history"] = []
        
        analytics["sentiment_history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment": analysis["sentiment"]
        })
        
        # Keep last 100 sentiments
        if len(analytics["sentiment_history"]) > 100:
            analytics["sentiment_history"] = analytics["sentiment_history"][-100:]
        
        # Save
        DataManager.save_json(filename, analytics)
    
    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get recent conversations for user"""
        filename = f"conversations/{user_id}_conversations.json"
        try:
            data = DataManager.load_json(filename)
            conversations = data.get("conversations", [])
            return conversations[-limit:]
        except:
            return []
    
    def get_user_analytics(self, user_id: str) -> Dict:
        """Get analytics for user"""
        filename = f"analytics/{user_id}_analytics.json"
        try:
            return DataManager.load_json(filename)
        except:
            return {}
