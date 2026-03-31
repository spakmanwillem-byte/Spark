from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
from datetime import datetime, timedelta

router = APIRouter()

class QuizQuestion(BaseModel):
    card_id: str
    question: str
    expected_layer: str
    user_answer: str

class QuizResult(BaseModel):
    card_id: str
    user_id: str
    correct: bool
    score: float

@router.post("/quiz/submit")
async def submit_quiz(result: QuizResult):
    """Submit quiz result and update user progress"""
    try:
        kb_file = Path("/app/backend/data/learned_knowledge/knowledge_base.json")
        with open(kb_file, 'r') as f:
            kb_data = json.load(f)
        
        entries = kb_data.get("knowledge_entries", [])
        card = next((e for e in entries if e["id"] == result.card_id), None)
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Update learning progress
        if "learning" not in card:
            card["learning"] = {"user_progress": {}}
        
        if result.user_id not in card["learning"]["user_progress"]:
            card["learning"]["user_progress"][result.user_id] = {
                "times_practiced": 0,
                "correct_answers": 0,
                "total_attempts": 0,
                "mastery_level": 0
            }
        
        progress = card["learning"]["user_progress"][result.user_id]
        progress["times_practiced"] += 1
        progress["total_attempts"] += 1
        if result.correct:
            progress["correct_answers"] += 1
        
        # Calculate mastery level
        progress["mastery_level"] = min(100, int((progress["correct_answers"] / progress["total_attempts"]) * 100))
        progress["last_practiced"] = datetime.now().isoformat()
        
        # Spaced repetition: next review date
        if result.correct:
            days_to_add = min(30, progress["times_practiced"] * 2)
        else:
            days_to_add = 1
        
        progress["next_review"] = (datetime.now() + timedelta(days=days_to_add)).isoformat()
        
        # Save
        with open(kb_file, 'w') as f:
            json.dump(kb_data, f, indent=2)
        
        return {
            "success": True,
            "mastery_level": progress["mastery_level"],
            "next_review": progress["next_review"],
            "xp_earned": 10 if result.correct else 2
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quiz/due/{user_id}")
async def get_due_cards(user_id: str):
    """Get cards due for review (spaced repetition)"""
    try:
        kb_file = Path("/app/backend/data/learned_knowledge/knowledge_base.json")
        with open(kb_file, 'r') as f:
            kb_data = json.load(f)
        
        entries = kb_data.get("knowledge_entries", [])
        due_cards = []
        
        now = datetime.now()
        
        for card in entries:
            learning = card.get("learning", {})
            user_progress = learning.get("user_progress", {}).get(user_id)
            
            if user_progress:
                next_review = user_progress.get("next_review")
                if next_review:
                    review_date = datetime.fromisoformat(next_review)
                    if review_date <= now:
                        due_cards.append({
                            "id": card["id"],
                            "begrip": card["begrip"],
                            "mastery_level": user_progress.get("mastery_level", 0)
                        })
        
        return {"success": True, "due_cards": due_cards, "count": len(due_cards)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/{user_id}")
async def get_learning_progress(user_id: str):
    """Get user's overall learning progress"""
    try:
        kb_file = Path("/app/backend/data/learned_knowledge/knowledge_base.json")
        with open(kb_file, 'r') as f:
            kb_data = json.load(f)
        
        entries = kb_data.get("knowledge_entries", [])
        
        total_cards = len(entries)
        practiced_cards = 0
        mastered_cards = 0
        total_mastery = 0
        
        for card in entries:
            learning = card.get("learning", {})
            user_progress = learning.get("user_progress", {}).get(user_id)
            
            if user_progress:
                practiced_cards += 1
                mastery = user_progress.get("mastery_level", 0)
                total_mastery += mastery
                if mastery >= 80:
                    mastered_cards += 1
        
        avg_mastery = total_mastery / practiced_cards if practiced_cards > 0 else 0
        
        return {
            "success": True,
            "total_cards": total_cards,
            "practiced_cards": practiced_cards,
            "mastered_cards": mastered_cards,
            "average_mastery": round(avg_mastery, 1),
            "completion_percentage": round((practiced_cards / total_cards) * 100, 1)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
