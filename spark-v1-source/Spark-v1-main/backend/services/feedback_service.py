from typing import Dict, List, Optional
from datetime import datetime
from utils.data_manager import DataManager
from services.knowledge_service import KnowledgeService
from models.knowledge import KnowledgeCreate
import uuid

class FeedbackService:
    @staticmethod
    def detect_poor_response(response: str) -> bool:
        """
        Detect if Spark gave a poor/generic response
        """
        poor_patterns = [
            "dat weet ik niet",
            "ik weet het antwoord nog niet",
            "dat is een goede vraag",
            "kun je het me leren",
            "kan je het me leren",
            "vertel me meer",
            "geen idee"
        ]
        
        response_lower = response.lower()
        
        # Check for poor patterns
        if any(pattern in response_lower for pattern in poor_patterns):
            return True
        
        # Very short responses (less than 10 words)
        if len(response.split()) < 10 and "?" in response:
            return True
        
        return False
    
    @staticmethod
    def log_feedback(
        user_id: str,
        user_naam: str,
        question: str,
        spark_answer: str,
        conversation_id: str,
        status: str = "poor"
    ):
        """
        Log a feedback item for review
        """
        feedback_id = f"fb-{str(uuid.uuid4())[:8]}"
        
        feedback_item = {
            "id": feedback_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "user_naam": user_naam,
            "question": question,
            "spark_answer": spark_answer,
            "status": status,  # poor, ok, good
            "improved_answer": None,
            "learned": False,
            "conversation_id": conversation_id
        }
        
        # Load existing feedback
        filename = "feedback/feedback_log.json"
        try:
            data = DataManager.load_json(filename)
            items = data.get("feedback_items", [])
        except:
            items = []
        
        # Add new item
        items.append(feedback_item)
        
        # Keep last 500 items
        if len(items) > 500:
            items = items[-500:]
        
        # Save
        data = {
            "feedback_items": items,
            "total_items": len(items),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        DataManager.save_json(filename, data)
        
        return feedback_item
    
    @staticmethod
    def get_all_feedback(filter_status: Optional[str] = None) -> List[Dict]:
        """
        Get all feedback items
        Optionally filter by status: poor, ok, good
        """
        filename = "feedback/feedback_log.json"
        try:
            data = DataManager.load_json(filename)
            items = data.get("feedback_items", [])
            
            if filter_status:
                items = [item for item in items if item.get("status") == filter_status]
            
            # Sort by timestamp (newest first)
            items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return items
        except:
            return []
    
    @staticmethod
    def improve_answer(feedback_id: str, improved_answer: str, user_id: str):
        """
        Improve a feedback item and optionally teach Spark
        """
        filename = "feedback/feedback_log.json"
        try:
            data = DataManager.load_json(filename)
            items = data.get("feedback_items", [])
        except:
            return {"success": False, "message": "Feedback not found"}
        
        # Find item
        for item in items:
            if item["id"] == feedback_id:
                item["improved_answer"] = improved_answer
                item["improved_by"] = user_id
                item["improved_at"] = datetime.utcnow().isoformat()
                item["status"] = "good"
                
                # Save updated feedback
                data["feedback_items"] = items
                data["last_updated"] = datetime.utcnow().isoformat()
                DataManager.save_json(filename, data)
                
                return {
                    "success": True,
                    "message": "Answer improved",
                    "item": item
                }
        
        return {"success": False, "message": "Feedback item not found"}
    
    @staticmethod
    def teach_spark(feedback_id: str):
        """
        Teach Spark the improved answer by adding to knowledge base
        """
        filename = "feedback/feedback_log.json"
        try:
            data = DataManager.load_json(filename)
            items = data.get("feedback_items", [])
        except:
            return {"success": False, "message": "Feedback not found"}
        
        # Find item
        for item in items:
            if item["id"] == feedback_id:
                if not item.get("improved_answer"):
                    return {"success": False, "message": "No improved answer to teach"}
                
                if item.get("learned"):
                    return {"success": False, "message": "Already taught"}
                
                # Add to knowledge base
                question = item["question"]
                answer = item["improved_answer"]
                
                # Try to parse as "X is Y" format
                if " is " in answer:
                    parts = answer.split(" is ", 1)
                    begrip = parts[0].strip()
                    betekenis = parts[1].strip()
                else:
                    # Use question as begrip
                    begrip = question.replace("Wat is", "").replace("?", "").strip()
                    betekenis = answer
                
                # Add to knowledge
                KnowledgeService.add_knowledge(KnowledgeCreate(
                    begrip=begrip,
                    betekenis=betekenis,
                    bron=item["user_naam"],
                    categorie="feedback_learned"
                ))
                
                # Mark as learned
                item["learned"] = True
                item["learned_at"] = datetime.utcnow().isoformat()
                
                # Save
                data["feedback_items"] = items
                DataManager.save_json(filename, data)
                
                return {
                    "success": True,
                    "message": f"Taught Spark: {begrip} = {betekenis}",
                    "knowledge": {"begrip": begrip, "betekenis": betekenis}
                }
        
        return {"success": False, "message": "Feedback item not found"}
    
    @staticmethod
    def get_stats() -> Dict:
        """
        Get feedback statistics
        """
        filename = "feedback/feedback_log.json"
        try:
            data = DataManager.load_json(filename)
            items = data.get("feedback_items", [])
        except:
            return {"total": 0, "poor": 0, "ok": 0, "good": 0, "learned": 0}
        
        stats = {
            "total": len(items),
            "poor": len([i for i in items if i.get("status") == "poor"]),
            "ok": len([i for i in items if i.get("status") == "ok"]),
            "good": len([i for i in items if i.get("status") == "good"]),
            "learned": len([i for i in items if i.get("learned")])
        }
        
        # Calculate improvement rate
        if stats["total"] > 0:
            stats["improvement_rate"] = round((stats["learned"] / stats["total"]) * 100, 1)
        else:
            stats["improvement_rate"] = 0
        
        return stats
