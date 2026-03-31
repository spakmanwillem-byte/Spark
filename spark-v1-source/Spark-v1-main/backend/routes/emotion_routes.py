"""
Emotion Routes - API endpoints voor emotie beheer
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.emotion_service import EmotionService
from services.emotion_stats import EmotionStats

router = APIRouter(prefix="/emotions", tags=["emotions"])


class EmotionUpdate(BaseModel):
    state: str = Field(..., description="Main emotion state")
    sub_state: Optional[str] = Field(None, description="Sub-emotion")
    intensity: float = Field(0.5, ge=0.0, le=1.0, description="Intensity (0-1)")
    triggered_by: str = Field("manual", description="What triggered this emotion")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes (None = permanent)")


@router.get("/current")
async def get_current_emotion():
    """Haal de huidige emotie van Spark op"""
    try:
        emotion = EmotionService.get_current_emotion()
        return {"success": True, "emotion": emotion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_emotions():
    """Haal alle beschikbare emoties op"""
    try:
        emotions = EmotionService.get_all_emotions()
        return {"success": True, "emotions": emotions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_emotion_stats():
    """Haal emotie statistieken op"""
    try:
        stats = EmotionService.get_emotion_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/xp-config")
async def get_xp_growth_config():
    """Haal XP-groei configuratie op"""
    try:
        config = EmotionService.get_xp_growth_config()
        return {"success": True, "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set")
async def set_emotion(emotion: EmotionUpdate):
    """
    Stel een nieuwe emotie in voor Spark (Admin only)
    """
    try:
        new_emotion = EmotionService.set_emotion(
            state=emotion.state,
            sub_state=emotion.sub_state,
            intensity=emotion.intensity,
            triggered_by=emotion.triggered_by,
            duration_minutes=emotion.duration_minutes
        )
        return {"success": True, "emotion": new_emotion}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_emotion():
    """Reset Spark naar neutrale emotie"""
    try:
        emotion = EmotionService.reset_to_neutral()
        return {"success": True, "emotion": emotion, "message": "Emotie gereset naar neutral"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{emotion_state}")
async def get_emotion_details(emotion_state: str):
    """Haal details op van een specifieke emotie"""
    try:
        details = EmotionService.get_emotion_details(emotion_state)
        if not details:
            raise HTTPException(status_code=404, detail=f"Emotion '{emotion_state}' not found")
        return {"success": True, "emotion": emotion_state, "details": details}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}")
async def get_emotion_history(user_id: str, limit: int = 100):
    """Get user's emotion history"""
    try:
        events = EmotionStats.get_emotion_history(user_id, limit)
        return {
            "success": True,
            "events": events,
            "count": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary/{user_id}")
async def get_emotion_summary(user_id: str):
    """Get emotion summary statistics"""
    try:
        summary = EmotionStats.get_emotion_summary(user_id)
        averages = EmotionStats.get_average_scores(user_id)
        
        return {
            "success": True,
            "summary": summary,
            "averages": averages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{user_id}")
async def get_emotion_patterns(user_id: str):
    """Get emotion patterns with topic analysis"""
    try:
        events = EmotionStats.get_emotion_history(user_id, limit=500)
        
        # Analyze patterns
        topic_emotions = {}
        
        for event in events:
            topics = event.get('topics', []) + [{'topic': t} for t in event.get('general_topics', [])]
            emotion = event.get('emotion')
            
            for topic_data in topics:
                topic = topic_data.get('topic') if isinstance(topic_data, dict) else topic_data
                if topic:
                    if topic not in topic_emotions:
                        topic_emotions[topic] = {
                            'blij': 0,
                            'boos': 0,
                            'bang': 0,
                            'bedroefd': 0,
                            'total': 0
                        }
                    
                    topic_emotions[topic][emotion] = topic_emotions[topic].get(emotion, 0) + 1
                    topic_emotions[topic]['total'] += 1
        
        # Sort by total occurrences
        patterns = []
        for topic, emotions in topic_emotions.items():
            dominant_emotion = max(emotions.items(), key=lambda x: x[1] if x[0] != 'total' else 0)
            patterns.append({
                'topic': topic,
                'dominant_emotion': dominant_emotion[0],
                'count': dominant_emotion[1],
                'total_mentions': emotions['total'],
                'emotions': emotions
            })
        
        patterns.sort(key=lambda x: x['total_mentions'], reverse=True)
        
        return {
            "success": True,
            "patterns": patterns[:20],  # Top 20
            "total_events": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
