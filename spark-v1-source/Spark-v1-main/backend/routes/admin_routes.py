"""
Admin Routes - For managing personality, achievements, etc.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.personality_service import PersonalityService
from services.achievement_service import AchievementService
from services.conversation_cache_service import ConversationCacheService
from services.summarization_service import SummarizationService

router = APIRouter()


# Pydantic models


class KnowledgeFeedback(BaseModel):
    helpful: bool

class NormCreate(BaseModel):
    norm: str
    beschrijving: str
    belangrijkheid: int
    voorbeelden: Optional[List[str]] = []


class ValueCreate(BaseModel):
    waarde: str
    beschrijving: str
    belangrijkheid: int
    voorbeelden: Optional[List[str]] = []


class BijbelItemCreate(BaseModel):
    naam: str
    beschrijving: str


class AchievementCreate(BaseModel):
    icoon: str
    onderwerp: str
    te_doen: str
    prijs: int


# Norms & Values routes
@router.get("/personality/norms")
async def get_norms():
    """Get all norms"""
    return {"norms": PersonalityService.get_all_norms()}


@router.get("/personality/values")
async def get_values():
    """Get all values"""
    return {"values": PersonalityService.get_all_values()}


@router.post("/personality/norms")
async def add_norm(norm: NormCreate):
    """Add new norm (admin only)"""
    new_norm = PersonalityService.add_norm(
        norm=norm.norm,
        beschrijving=norm.beschrijving,
        belangrijkheid=norm.belangrijkheid,
        voorbeelden=norm.voorbeelden
    )
    return {"success": True, "norm": new_norm}


@router.post("/personality/values")
async def add_value(value: ValueCreate):
    """Add new value (admin only)"""
    new_value = PersonalityService.add_value(
        waarde=value.waarde,
        beschrijving=value.beschrijving,
        belangrijkheid=value.belangrijkheid,
        voorbeelden=value.voorbeelden
    )
    return {"success": True, "value": new_value}


@router.delete("/personality/norms/{norm_id}")
async def delete_norm(norm_id: str):
    """Delete norm (admin only)"""
    success = PersonalityService.delete_norm(norm_id)
    if success:
        return {"success": True, "message": "Norm deleted"}
    raise HTTPException(status_code=404, detail="Norm not found")


@router.put("/personality/norms/{norm_id}")
async def update_norm(norm_id: str, data: dict):
    """Update norm (admin only)"""
    updated = PersonalityService.update_norm(
        norm_id, 
        data.get("norm", ""),
        data.get("beschrijving", ""),
        data.get("belangrijkheid", 3),
        data.get("niveau", 3)
    )
    if updated:
        return {"success": True, "norm": updated}
    raise HTTPException(status_code=404, detail="Norm not found")


@router.delete("/personality/values/{value_id}")
async def delete_value(value_id: str):
    """Delete value (admin only)"""
    success = PersonalityService.delete_value(value_id)
    if success:
        return {"success": True, "message": "Value deleted"}

@router.put("/personality/values/{value_id}")
async def update_value(value_id: str, data: dict):
    """Update value (admin only)"""
    updated = PersonalityService.update_value(
        value_id,
        data.get("waarde", ""),
        data.get("beschrijving", ""),
        data.get("belangrijkheid", 3),
        data.get("niveau", 3)
    )
    if updated:
        return {"success": True, "value": updated}
    raise HTTPException(status_code=404, detail="Value not found")

    raise HTTPException(status_code=404, detail="Value not found")


# Bijbel routes
@router.get("/personality/bijbel")
async def get_bijbel_items():
    """Get all bijbel items"""
    return {"items": PersonalityService.get_all_bijbel_items()}


@router.post("/personality/bijbel")
async def add_bijbel_item(item: BijbelItemCreate):
    """Add new bijbel item (admin only)"""
    new_item = PersonalityService.add_bijbel_item(
        naam=item.naam,
        beschrijving=item.beschrijving
    )
    return {"success": True, "item": new_item}


@router.delete("/personality/bijbel/{item_id}")
async def delete_bijbel_item(item_id: str):
    """Delete bijbel item (admin only)"""
    success = PersonalityService.delete_bijbel_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bijbel item not found")
    return {"success": True, "message": "Bijbel item deleted"}

@router.put("/personality/bijbel/{item_id}")
async def update_bijbel_item(item_id: str, data: dict):
    """Update bijbel item (admin only)"""
    updated = PersonalityService.update_bijbel_item(
        item_id,
        data.get("naam", ""),
        data.get("beschrijving", "")
    )
    if updated:
        return {"success": True, "item": updated}
    raise HTTPException(status_code=404, detail="Item not found")


# Achievements routes
@router.get("/achievements")
async def get_achievements():
    """Get all achievements"""
    return {"achievements": AchievementService.get_all_achievements()}


@router.get("/achievements/{user_id}")
async def get_user_achievements(user_id: str):
    """Get user's achievements and XP"""
    from services.achievement_service import AchievementService as NewAchievementService
    
    # Use NEW achievement service
    data = NewAchievementService.get_user_achievements(user_id)
    
    return {
        "success": True,
        **data
    }


@router.post("/achievements")
async def add_achievement(achievement: AchievementCreate):
    """Add new achievement (admin only)"""
    new_achievement = AchievementService.add_achievement(
        icoon=achievement.icoon,
        onderwerp=achievement.onderwerp,
        te_doen=achievement.te_doen,
        prijs=achievement.prijs
    )
    return {"success": True, "achievement": new_achievement}


@router.post("/achievements/{user_id}/unlock/{achievement_id}")
async def unlock_achievement(user_id: str, achievement_id: str):
    """Unlock achievement for user"""
    result = AchievementService.unlock_achievement(user_id, achievement_id)
    return result



# Knowledge CRUD routes
class KnowledgeCreate(BaseModel):
    begrip: str
    lagen: dict  # {laag1: str, laag2: str, laag3: str}
    tags: Optional[List[str]] = []
    belangrijkheid: Optional[int] = 3
    ws5: Optional[dict] = None  # {who, what, when, where, why, how}


@router.post("/knowledge")
async def add_knowledge(knowledge: dict):
    """Add new knowledge (admin only)"""
    from utils.data_manager import DataManager
    from datetime import datetime
    import uuid
    
    # Get admin info from request body
    admin_name = knowledge.get('admin_user_naam', 'Unknown Admin')
    admin_user_id = knowledge.get('admin_user_id')
    
    # Load current knowledge
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    
    if "knowledge_entries" not in data:
        data["knowledge_entries"] = []
    
    # Create new knowledge entry
    new_entry = {
        "id": str(uuid.uuid4())[:8],
        "begrip": knowledge.get("begrip"),
        "lagen": {
            "laag1": knowledge.get("lagen", {}).get("laag1", ""),
            "laag2": knowledge.get("lagen", {}).get("laag2", ""),
            "laag3": knowledge.get("lagen", {}).get("laag3", ""),
            "laag4": knowledge.get("lagen", {}).get("laag4", "")  # ✨ NEW
        },
        "tags": knowledge.get("tags", []),
        "topic": knowledge.get("topic", "algemeen"),  # ✨ NEW
        "belangrijkheid": knowledge.get("belangrijkheid", 3),
        "ws5": knowledge.get("ws5", {"who": "", "what": "", "when": "", "where": "", "why": "", "how": ""}),
        "geleerd_van": f"{admin_name} (handmatig)",
        "datum": datetime.now().isoformat(),
        "status": "active",
        # Admin tracking
        "created_by_admin": admin_name,
        "created_by_user_id": admin_user_id,
        "created_at": datetime.now().isoformat(),
        "created_via": "admin",  # How this knowledge was created
        "usage_count": 0,
        "feedback": {"helpful": 0, "not_helpful": 0}
    }
    
    data["knowledge_entries"].append(new_entry)
    DataManager.save_json("learned_knowledge/knowledge_base.json", data)
    
    return {"success": True, "knowledge": new_entry}


@router.patch("/knowledge/{knowledge_id}/trash")
async def move_to_trash(knowledge_id: str):
    """Move knowledge entry to trash (soft delete)"""
    from utils.data_manager import DataManager
    from services.action_logger import ActionLogger
    
    ActionLogger.log("TRASH_START", "knowledge", knowledge_id, {"status": "attempting"})
    
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    entries = data.get("knowledge_entries", [])
    
    found = False
    for entry in entries:
        if entry.get("id") == knowledge_id or entry.get("begrip") == knowledge_id:
            entry["status"] = "trash"
            entry["deleted_at"] = __import__('datetime').datetime.now().isoformat()
            found = True
            ActionLogger.log("TRASH", "knowledge", knowledge_id, {
                "begrip": entry.get("begrip"),
                "previous_status": entry.get("status", "active")
            }, success=True)
            break
    
    if not found:
        ActionLogger.log("TRASH", "knowledge", knowledge_id, {"error": "not found"}, success=False)
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    data["knowledge_entries"] = entries
    DataManager.save_json("learned_knowledge/knowledge_base.json", data)
    ActionLogger.log("SAVE", "knowledge_base", "file", {"action": "trash_save"})
    
    return {"success": True, "message": "Moved to trash"}

@router.patch("/knowledge/{knowledge_id}/restore")
async def restore_from_trash(knowledge_id: str):
    """Restore knowledge entry from trash"""
    from utils.data_manager import DataManager
    from services.action_logger import ActionLogger
    
    ActionLogger.log("RESTORE_START", "knowledge", knowledge_id, {"status": "attempting"})
    
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    entries = data.get("knowledge_entries", [])
    
    found = False
    for entry in entries:
        if entry.get("id") == knowledge_id or entry.get("begrip") == knowledge_id:
            entry["status"] = "active"
            if "deleted_at" in entry:
                del entry["deleted_at"]
            found = True
            ActionLogger.log("RESTORE", "knowledge", knowledge_id, {
                "begrip": entry.get("begrip")
            }, success=True)
            break
    
    if not found:
        ActionLogger.log("RESTORE", "knowledge", knowledge_id, {"error": "not found"}, success=False)
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    data["knowledge_entries"] = entries
    DataManager.save_json("learned_knowledge/knowledge_base.json", data)
    ActionLogger.log("SAVE", "knowledge_base", "file", {"action": "restore_save"})
    
    return {"success": True, "message": "Restored from trash"}

@router.delete("/knowledge/{knowledge_id}/permanent")
async def delete_permanently(knowledge_id: str):
    """Permanently delete knowledge entry (cannot be undone)"""
    from utils.data_manager import DataManager
    from services.action_logger import ActionLogger
    
    ActionLogger.log("DELETE_PERMANENT_START", "knowledge", knowledge_id, {"status": "attempting"})
    
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    entries = data.get("knowledge_entries", [])
    
    # Only allow permanent delete if item is in trash
    entry_to_delete = None
    for entry in entries:
        if (entry.get("id") == knowledge_id or entry.get("begrip") == knowledge_id):
            if entry.get("status") != "trash":
                ActionLogger.log("DELETE_PERMANENT", "knowledge", knowledge_id, {
                    "error": "not in trash",
                    "current_status": entry.get("status")
                }, success=False)
                raise HTTPException(
                    status_code=400, 
                    detail="Item must be in trash before permanent deletion"
                )
            entry_to_delete = entry
            break
    
    if not entry_to_delete:
        ActionLogger.log("DELETE_PERMANENT", "knowledge", knowledge_id, {"error": "not found"}, success=False)
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    ActionLogger.log("DELETE_PERMANENT", "knowledge", knowledge_id, {
        "begrip": entry_to_delete.get("begrip"),
        "entries_before": len(entries)
    }, success=True)
    
    entries.remove(entry_to_delete)
    data["knowledge_entries"] = entries
    DataManager.save_json("learned_knowledge/knowledge_base.json", data)
    
    ActionLogger.log("SAVE", "knowledge_base", "file", {"action": "permanent_delete_save", "entries_after": len(entries)})
    
    return {"success": True, "message": "Permanently deleted"}

# DEBUG / LOGGING ENDPOINTS
@router.get("/debug/logs")
async def get_action_logs(limit: int = 50):
    """Get recent action logs for debugging"""
    from services.action_logger import ActionLogger
    
    logs = ActionLogger.get_recent_logs(limit=limit)
    return {"logs": logs, "count": len(logs)}

@router.delete("/debug/logs")
async def clear_action_logs():
    """Clear all action logs (admin only)"""
    from services.action_logger import ActionLogger
    ActionLogger.clear_logs()
    return {"success": True, "message": "Logs cleared"}


# SIMPLE HARD DELETE (no trash system)
@router.delete("/knowledge/{knowledge_id}")
async def delete_knowledge_simple(knowledge_id: str):
    """
    Simple hard delete - removes knowledge immediately
    """
    from utils.data_manager import DataManager
    from services.action_logger import ActionLogger
    
    ActionLogger.log("DELETE_START", "knowledge", knowledge_id, {"type": "hard_delete"})
    
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    entries = data.get("knowledge_entries", [])
    
    # Find entry
    entry_to_delete = None
    for entry in entries:
        if entry.get("id") == knowledge_id or entry.get("begrip") == knowledge_id:
            entry_to_delete = entry
            break
    
    if not entry_to_delete:
        ActionLogger.log("DELETE", "knowledge", knowledge_id, {"error": "not found"}, success=False)
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    # Remove from list
    new_entries = [e for e in entries if e.get("id") != knowledge_id and e.get("begrip") != knowledge_id]
    
    ActionLogger.log("DELETE", "knowledge", knowledge_id, {
        "begrip": entry_to_delete.get("begrip"),
        "entries_before": len(entries),
        "entries_after": len(new_entries)
    }, success=True)
    
    # Save
    data["knowledge_entries"] = new_entries
    DataManager.save_json("learned_knowledge/knowledge_base.json", data)
    ActionLogger.log("SAVE", "knowledge_base", "file", {"action": "delete_save"})
    
    return {"success": True, "message": "Knowledge deleted", "id": knowledge_id}


@router.put("/knowledge/{knowledge_id}")
async def update_knowledge(knowledge_id: str, knowledge_update: dict):
    """Update a knowledge entry (admin only)"""
    from utils.data_manager import DataManager
    from services.achievement_service import AchievementService
    from services.action_logger import ActionLogger
    from datetime import datetime
    
    # Get admin info from request body
    admin_name = knowledge_update.get('admin_user_naam', 'Unknown Admin')
    admin_user_id = knowledge_update.get('admin_user_id')
    
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    entries = data.get("knowledge_entries", [])
    
    # Find and update the entry
    updated = False
    xp_result = None
    
    for entry in entries:
        if entry.get("id") == knowledge_id:
            # Check if this is a draft → active transition (Snap approval)
            old_status = entry.get("status", "active")
            is_snap_approval = (
                old_status == "draft" and 
                not entry.get("xp_awarded", False) and
                entry.get("detected_by") is not None
            )
            
            # Update fields
            if "begrip" in knowledge_update:
                entry["begrip"] = knowledge_update["begrip"]
            if "lagen" in knowledge_update:
                # Ensure all 4 layers exist
                entry["lagen"] = {
                    "laag1": knowledge_update["lagen"].get("laag1", ""),
                    "laag2": knowledge_update["lagen"].get("laag2", ""),
                    "laag3": knowledge_update["lagen"].get("laag3", ""),
                    "laag4": knowledge_update["lagen"].get("laag4", "")  # ✨ NEW
                }
            if "tags" in knowledge_update:
                entry["tags"] = knowledge_update["tags"]
            if "topic" in knowledge_update:  # ✨ NEW
                entry["topic"] = knowledge_update["topic"]
            if "belangrijkheid" in knowledge_update:
                entry["belangrijkheid"] = knowledge_update["belangrijkheid"]
            if "ws5" in knowledge_update:
                entry["ws5"] = knowledge_update["ws5"]
            
            # Update status if provided
            if "status" in knowledge_update:
                entry["status"] = knowledge_update["status"]
            
            # Check if snap is being approved (has content now)
            has_content = entry.get("lagen", {}).get("laag1", "").strip() != "" and \
                         not entry.get("lagen", {}).get("laag1", "").startswith("[Knowledge snap:")
            
            # If snap is being filled in with real content, mark as active
            if is_snap_approval and has_content:
                entry["status"] = "active"
                
                # Award XP to the user who created the snap
                detected_by = entry.get("detected_by")
                if detected_by:
                    # Map naam → user_id
                    user_id = AchievementService.get_user_id_by_name(detected_by)
                    
                    if user_id:
                        # Award XP for snap → knowledge
                        xp_result = AchievementService.award_xp_for_event(user_id, "snap_to_knowledge")
                        
                        if xp_result.get("success"):
                            # Mark as XP awarded to prevent duplicates
                            entry["xp_awarded"] = True
                            entry["xp_awarded_to"] = user_id
                            entry["xp_awarded_at"] = __import__('datetime').datetime.now().isoformat()
                            
                            ActionLogger.log("XP_AWARDED", "snap_approval", knowledge_id, {
                                "user_id": user_id,
                                "user_naam": detected_by,
                                "xp": xp_result.get("xp_awarded"),
                                "begrip": entry.get("begrip")
                            })
                    else:
                        ActionLogger.log("XP_FAILED", "user_not_found", knowledge_id, {
                            "detected_by": detected_by,
                            "reason": "Could not map naam to user_id"
                        })
            
            # Mark as answered if it was a user question
            if entry.get("lagen", {}).get("laag1") and "user-vraag" in entry.get("tags", []):
                entry["tags"] = [t for t in entry["tags"] if t != "user-vraag"]
                if "beantwoord" not in entry.get("tags", []):
                    entry["tags"].append("beantwoord")
            
            # Track who edited this
            entry["last_edited_by_admin"] = admin_name
            entry["last_edited_by_user_id"] = admin_user_id
            entry["last_edited_at"] = datetime.now().isoformat()
            
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    # Save updated knowledge base
    data["knowledge_entries"] = entries
    DataManager.save_json("learned_knowledge/knowledge_base.json", data)
    
    # Return response with XP info if awarded
    response = {
        "success": True, 
        "message": "Knowledge updated"
    }
    
    if xp_result and xp_result.get("success"):
        response["xp_awarded"] = {
            "xp": xp_result.get("xp_awarded"),
            "total_xp": xp_result.get("total_xp"),
            "level": xp_result.get("new_level"),
            "level_up": xp_result.get("level_up"),
            "message": f"🎉 {xp_result.get('xp_awarded')} XP toegekend!"
        }
    
    return response
# Knowledge Feedback & Stats Routes
@router.post("/knowledge/{knowledge_id}/feedback")
async def record_knowledge_feedback(knowledge_id: str, feedback: KnowledgeFeedback):
    """
    Record user feedback on a knowledge entry
    
    Args:
        knowledge_id: ID of the knowledge entry
        feedback.helpful: True if helpful, False if not
    """
    from services.knowledge_service import KnowledgeService
    
    success = KnowledgeService.record_feedback(knowledge_id, feedback.helpful)
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    return {
        "success": True,
        "message": "Feedback opgeslagen",
        "knowledge_id": knowledge_id,
        "helpful": feedback.helpful
    }


@router.get("/knowledge/{knowledge_id}/stats")
async def get_knowledge_stats(knowledge_id: str):
    """
    Get usage statistics for a knowledge entry
    
    Returns usage_count, feedback scores, etc.
    """
    from services.knowledge_service import KnowledgeService
    
    entries = KnowledgeService.get_all_knowledge()
    entry = next((e for e in entries if e.get("id") == knowledge_id), None)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    return {
        "success": True,
        "stats": {
            "knowledge_id": knowledge_id,
            "begrip": entry.get("begrip"),
            "usage_count": entry.get("usage_count", 0),
            "feedback": entry.get("feedback", {
                "helpful": 0,
                "not_helpful": 0,
                "score": 0.5
            }),
            "belangrijkheid": entry.get("belangrijkheid", 3)
        }
    }

    
    return {"success": True, "message": "Knowledge updated"}


# Cache Statistics endpoint
@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get conversation cache statistics.
    
    Returns cache performance metrics:
    - Hit rate
    - Active sessions
    - Memory usage
    - Total requests
    """
    try:
        cache_service = ConversationCacheService()
        stats = cache_service.get_cache_stats()
        
        return {
            "success": True,
            "stats": stats,
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")



# Summarization endpoints
@router.post("/summarize/{user_id}")
async def generate_summary(user_id: str, limit: int = 100):
    """
    Generate conversation summary for a user.
    
    Args:
        user_id: User identifier
        limit: Max messages to analyze (default: 100)
    
    Returns:
        Generated summary
    """
    try:
        summarization = SummarizationService()
        
        # Generate summary
        summary = summarization.summarize_user_history(
            user_id=user_id,
            limit=limit
        )
        
        if summary is None:
            return {
                "success": False,
                "message": "Insufficient data to generate summary (need at least 5 messages)"
            }
        
        # Store summary
        summarization.store_summary(user_id, summary)
        
        return {
            "success": True,
            "summary": summary.to_dict(),
            "message": f"Summary generated for {summary.total_messages} messages"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")


@router.get("/summaries/{user_id}")
async def get_user_summaries(user_id: str):
    """
    Get all summaries for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        List of summaries
    """
    try:
        summarization = SummarizationService()
        summaries = summarization.get_summaries(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "summary_count": len(summaries),
            "summaries": summaries
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summaries: {str(e)}")


@router.get("/summaries/{user_id}/latest")
async def get_latest_summary(user_id: str):
    """
    Get most recent summary for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        Latest summary
    """
    try:
        summarization = SummarizationService()
        summary = summarization.get_latest_summary(user_id)
        
        if summary is None:
            return {
                "success": False,
                "message": "No summaries found for this user"
            }
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")




# ============================================================================
# KNOWLEDGE REVIEW ENDPOINTS - Guest Contributions & Pending Confirmation
# ============================================================================

@router.get("/knowledge/review/pending")
async def get_pending_knowledge():
    """
    Get all knowledge entries that need review:
    - guest_contribution: From anonymous users
    - pending_confirmation: Possible duplicates that need Willem's decision
    """
    try:
        from utils.data_manager import DataManager
        
        kb = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = kb.get("knowledge_entries", [])
        
        # Filter entries that need review
        guest_contributions = [
            e for e in entries 
            if e.get("status") == "guest_contribution"
        ]
        
        pending_confirmation = [
            e for e in entries 
            if e.get("status") == "pending_confirmation"
        ]
        
        # Sort by created_at (newest first)
        guest_contributions.sort(
            key=lambda x: x.get("metadata", {}).get("created_at", ""), 
            reverse=True
        )
        pending_confirmation.sort(
            key=lambda x: x.get("metadata", {}).get("created_at", ""), 
            reverse=True
        )
        
        return {
            "guest_contributions": guest_contributions,
            "pending_confirmation": pending_confirmation,
            "counts": {
                "guest": len(guest_contributions),
                "pending": len(pending_confirmation),
                "total": len(guest_contributions) + len(pending_confirmation)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending knowledge: {str(e)}")


@router.put("/knowledge/{knowledge_id}/approve")
async def approve_knowledge(knowledge_id: str):
    """
    Approve a guest contribution or pending entry.
    Changes status to 'draft' so Willem can fill it in later.
    """
    try:
        from utils.data_manager import DataManager
        
        kb = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = kb.get("knowledge_entries", [])
        
        # Find entry
        entry = next((e for e in entries if e.get("id") == knowledge_id), None)
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        
        # Update status
        old_status = entry.get("status")
        entry["status"] = "draft"
        
        # Add approval metadata
        from datetime import datetime
        if "metadata" not in entry:
            entry["metadata"] = {}
        entry["metadata"]["approved_at"] = datetime.now().isoformat()
        entry["metadata"]["approved_from"] = old_status
        
        # Save
        DataManager.save_json("learned_knowledge/knowledge_base.json", kb)
        
        return {"success": True, "message": f"Entry '{entry.get('begrip')}' approved", "entry": entry}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve: {str(e)}")


@router.put("/knowledge/{knowledge_id}/reject")
async def reject_knowledge(knowledge_id: str):
    """
    Reject a guest contribution or pending entry.
    Removes it from the knowledge base.
    """
    try:
        from utils.data_manager import DataManager
        
        kb = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = kb.get("knowledge_entries", [])
        
        # Find and remove entry
        entry = next((e for e in entries if e.get("id") == knowledge_id), None)
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        
        begrip = entry.get("begrip")
        entries.remove(entry)
        kb["knowledge_entries"] = entries
        
        # Save
        DataManager.save_json("learned_knowledge/knowledge_base.json", kb)
        
        return {"success": True, "message": f"Entry '{begrip}' rejected and removed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject: {str(e)}")


@router.put("/knowledge/{knowledge_id}/confirm-different")
async def confirm_different(knowledge_id: str):
    """
    For pending_confirmation entries: Confirm this is DIFFERENT from the similar entry.
    Approve it as a new entry (status = draft).
    """
    try:
        from utils.data_manager import DataManager
        from datetime import datetime
        
        kb = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = kb.get("knowledge_entries", [])
        
        # Find entry
        entry = next((e for e in entries if e.get("id") == knowledge_id), None)
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        
        # Update status to draft
        entry["status"] = "draft"
        
        # Add confirmation metadata
        if "metadata" not in entry:
            entry["metadata"] = {}
        entry["metadata"]["confirmed_different"] = True
        entry["metadata"]["confirmed_at"] = datetime.now().isoformat()
        
        # Remove confirmation_needed flag
        if "confirmation_needed" in entry:
            del entry["confirmation_needed"]
        
        # Save
        DataManager.save_json("learned_knowledge/knowledge_base.json", kb)
        
        return {"success": True, "message": f"'{entry.get('begrip')}' confirmed as different", "entry": entry}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to confirm different: {str(e)}")


@router.put("/knowledge/{knowledge_id}/confirm-same")
async def confirm_same(knowledge_id: str):
    """
    For pending_confirmation entries: Confirm this is the SAME as the similar entry.
    Reject this entry (it's a duplicate).
    """
    try:
        from utils.data_manager import DataManager
        
        kb = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = kb.get("knowledge_entries", [])
        
        # Find and remove entry (it's a duplicate)
        entry = next((e for e in entries if e.get("id") == knowledge_id), None)
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge entry not found")
        
        begrip = entry.get("begrip")
        similar_to = entry.get("confirmation_needed", {}).get("similar_to", "onbekend")
        
        entries.remove(entry)
        kb["knowledge_entries"] = entries
        
        # Save
        DataManager.save_json("learned_knowledge/knowledge_base.json", kb)
        
        return {
            "success": True, 
            "message": f"'{begrip}' confirmed as duplicate of '{similar_to}' and removed"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to confirm same: {str(e)}")
