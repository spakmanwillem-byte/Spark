"""
Lightweight Conversation State Manager
Tracks only the last question Spark asked per session
"""
from datetime import datetime, timedelta
from typing import Optional


class ConversationStateManager:
    """
    Minimal conversation state tracking
    Stores: last_question per session + custom state for triggers/flows
    """
    
    _states = {}  # session_id: {"last_question": str, "timestamp": datetime, "custom": {}}
    
    @staticmethod
    def set_state(session_id: str, key: str, value):
        """
        Set custom state for a session
        
        Args:
            session_id: User/session identifier
            key: State key
            value: State value
        """
        if session_id not in ConversationStateManager._states:
            ConversationStateManager._states[session_id] = {
                "custom": {},
                "timestamp": datetime.now()
            }
        
        ConversationStateManager._states[session_id]["custom"][key] = value
        ConversationStateManager._states[session_id]["timestamp"] = datetime.now()
    
    @staticmethod
    def get_state(session_id: str, key: str):
        """
        Get custom state for a session
        
        Returns:
            State value or None if not found
        """
        state = ConversationStateManager._states.get(session_id)
        if not state:
            return None
        
        # Check if expired (5 minutes)
        if datetime.now() - state["timestamp"] > timedelta(minutes=5):
            ConversationStateManager.clear_state(session_id, key)
            return None
        
        return state.get("custom", {}).get(key)
    
    @staticmethod
    def clear_state(session_id: str, key: str):
        """Clear specific state key"""
        state = ConversationStateManager._states.get(session_id)
        if state and "custom" in state and key in state["custom"]:
            del state["custom"][key]
    
    @staticmethod
    def set_last_question(session_id: str, question_type: str):
        """
        Store that Spark asked a question
        
        Args:
            session_id: User/session identifier
            question_type: Type of question ("how_are_you", "greeting", etc.)
        """
        ConversationStateManager._states[session_id] = {
            "last_question": question_type,
            "timestamp": datetime.now()
        }
        print(f"[STATE] Stored last_question: {question_type} for session {session_id[:8]}")
    
    @staticmethod
    def get_last_question(session_id: str) -> Optional[str]:
        """
        Get the last question Spark asked (if within timeout)
        
        Args:
            session_id: User/session identifier
            
        Returns:
            Question type or None if expired/not found
        """
        state = ConversationStateManager._states.get(session_id)
        
        if not state:
            return None
        
        # Expire after 2 minutes (user took too long to answer)
        if datetime.now() - state["timestamp"] > timedelta(minutes=2):
            ConversationStateManager.clear_last_question(session_id)
            return None
        
        return state["last_question"]
    
    @staticmethod
    def clear_last_question(session_id: str):
        """
        Clear the conversation state (after handling answer)
        
        Args:
            session_id: User/session identifier
        """
        if session_id in ConversationStateManager._states:
            del ConversationStateManager._states[session_id]
            print(f"[STATE] Cleared last_question for session {session_id[:8]}")
