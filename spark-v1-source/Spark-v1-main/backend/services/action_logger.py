"""
Action Logger - Logs all important actions for debugging
Live viewable in Admin Debug Tab
"""
import json
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque
from utils.paths import PATHS


class ActionLogger:
    """
    Central logger for all Spark actions
    Keeps last 100 actions in memory + saves to file
    """
    
    _log_buffer = deque(maxlen=100)  # Keep last 100 actions in memory
    _log_file = PATHS["action_log"]  # Cross-platform path
    
    @classmethod
    def log(cls, action: str, entity_type: str, entity_id: str, details: Optional[Dict] = None, success: bool = True):
        """
        Log an action
        
        Args:
            action: DELETE, RESTORE, CREATE, UPDATE, etc.
            entity_type: knowledge, norm, value, bijbel, etc.
            entity_id: ID of the entity
            details: Additional info
            success: Whether the action succeeded
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
            "success": success
        }
        
        # Add to memory buffer
        cls._log_buffer.append(log_entry)
        
        # Also print to console (visible in supervisor logs)
        status = "✅" if success else "❌"
        print(f"{status} [{action}] {entity_type} {entity_id}")
        
        # Save to file (async, don't block)
        try:
            cls._save_to_file()
        except Exception as e:
            print(f"Warning: Could not save log to file: {e}")
    
    @classmethod
    def _save_to_file(cls):
        """Save log buffer to file"""
        cls._log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing logs
        if cls._log_file.exists():
            try:
                with open(cls._log_file, 'r') as f:
                    existing_logs = json.load(f)
            except:
                existing_logs = []
        else:
            existing_logs = []
        
        # Append new logs (keep last 200 total)
        all_logs = existing_logs + list(cls._log_buffer)
        all_logs = all_logs[-200:]  # Keep last 200 only
        
        # Save
        with open(cls._log_file, 'w') as f:
            json.dump(all_logs, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def get_recent_logs(cls, limit: int = 50) -> List[Dict]:
        """Get recent logs (from memory buffer)"""
        logs = list(cls._log_buffer)
        return logs[-limit:]
    
    @classmethod
    def get_all_logs(cls) -> List[Dict]:
        """Get all logs (from file)"""
        if cls._log_file.exists():
            try:
                with open(cls._log_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    @classmethod
    def clear_logs(cls):
        """Clear all logs (admin only!)"""
        cls._log_buffer.clear()
        if cls._log_file.exists():
            cls._log_file.unlink()
        cls.log("CLEAR", "logs", "all", {"message": "All logs cleared"})
