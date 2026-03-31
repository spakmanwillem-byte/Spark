from fastapi import APIRouter, HTTPException
from models.message import ChatMessage, ChatResponse
from models.user import User
from services.spark_brain import SparkBrain
from services.auth_service import AuthService
from services.personal_info_extractor import PersonalInfoExtractor
from utils.data_manager import DataManager
from typing import Optional

from services.person_detection_service import PersonDetectionService
from services.person_card_service import PersonCardService
from services.intent_manager import detect_mode_switch, format_response
from services.trigger_service import get_trigger_service

router = APIRouter()
spark_brain = SparkBrain()
trigger_service = get_trigger_service()  # Simpele trigger check (greetings, etc.)

# In-memory session storage (simplified for MVP)
active_sessions = {}

# Store pending person suggestions per session
pending_person_suggestions = {}

@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Main chat endpoint
    """
    try:
        # Get user data if user_id provided
        user_data = None
        if message.user_id:
            users = DataManager.load_users()
            user_data = next((u for u in users if u["id"] == message.user_id), None)
            
            # Validate session BEFORE processing message
            if user_data:
                session_valid = AuthService.validate_session(user_data["id"])
                if not session_valid:
                    # Session expired - return logout message
                    return ChatResponse(
                        response="⏱️ Je sessie is verlopen na 5 minuten inactiviteit.\n\nLog opnieuw in met: 'Ik ben [naam], [sleutelwoord]'",
                        user_id=None,
                        user_gradatie=None,
                        context=None
                    )
                
                # 🔥 FIX: Update last_active voor elke chat message van ingelogde gebruiker
                from datetime import datetime
                for u in users:
                    if u["id"] == user_data["id"]:
                        u["last_active"] = datetime.utcnow().isoformat()
                        break
                DataManager.save_users(users)
        
        # Use message.user_id as session_id (works for both logged-in and anonymous users)
        session_id = message.user_id or "anonymous"
        
        # 🎯 INTENT DETECTION: Check for mode switches
        mode_result = detect_mode_switch(message.message, session_id)
        if mode_result.get("switched"):
            # User switched mode - return confirmation
            return ChatResponse(
                response=mode_result["message"],
                user_id=user_data.get("id") if user_data else None,
                user_gradatie=user_data.get("gradatie") if user_data else None,
                context=user_data if user_data else None
            )
        
        # ⚡ TRIGGER CHECK: Greetings, farewells, actions (VOOR brain processing)
        trigger_result = trigger_service.check_trigger(message.message)
        if trigger_result['triggered']:
            # Check if it's an action trigger
            if trigger_result.get('card_type') == 'action':
                # Import action handler (Core)
                from services.action_handler import get_action_handler
                action_handler = get_action_handler()
                
                # Execute action (pass user_id for notes)
                action_result = action_handler.execute_action(
                    action=trigger_result.get('action'),
                    user_input=trigger_result.get('user_input'),
                    response_config=trigger_result.get('response_config'),
                    user_id=user_data.get("id") if user_data else None
                )
                
                # Return action result
                return ChatResponse(
                    response=action_result['message'],
                    user_id=user_data.get("id") if user_data else None,
                    user_gradatie=user_data.get("gradatie") if user_data else None,
                    context=user_data if user_data else None
                )
            
            # Regular response trigger (greeting, farewell)
            return ChatResponse(
                response=trigger_result['response'],
                user_id=user_data.get("id") if user_data else None,
                user_gradatie=user_data.get("gradatie") if user_data else None,
                context=user_data if user_data else None
            )
        
        # 🔍 PERSON DETECTION: Check for pending confirmations
        if user_data and session_id in pending_person_suggestions:
            suggestion = pending_person_suggestions[session_id]
            
            # Check if user responds to suggestion
            msg_lower = message.message.lower()
            if 'ja' in msg_lower or 'graag' in msg_lower or 'ok' in msg_lower:
                # Create Person Card
                person_card = PersonCardService.create_person_card(
                    user_id=user_data["id"],
                    naam=suggestion['naam'],
                    relatie=suggestion.get('suggested_relatie'),
                    gradatie=PersonDetectionService.suggest_gradatie_from_relatie(suggestion.get('suggested_relatie')),
                    is_user=suggestion.get('is_user', False),
                    tags=[suggestion.get('suggested_relatie')] if suggestion.get('suggested_relatie') else []
                )
                
                # Clear pending
                del pending_person_suggestions[session_id]
                
                # Return confirmation
                response = f"✅ Person Card aangemaakt voor **{suggestion['naam']}**!\n\n"
                response += f"Relatie: {person_card.get('relatie', 'onbekend')}\n"
                response += f"Gradatie: {person_card.get('gradatie')}\n\n"
                response += "Je kunt dit later aanpassen in de Person Cards tab."
                
                return ChatResponse(
                    response=response,
                    user_id=user_data["id"],
                    user_gradatie=user_data.get("gradatie"),
                    context=None
                )
            
            elif 'nee' in msg_lower or 'niet' in msg_lower:
                # Clear pending
                del pending_person_suggestions[session_id]
                
                return ChatResponse(
                    response="Oké, ik heb geen Person Card aangemaakt. 👍",
                    user_id=user_data["id"],
                    user_gradatie=user_data.get("gradatie"),
                    context=None
                )
        
        # Process message through Spark Brain (now returns tuple)
        response_text, updated_user_data = spark_brain.process_message(message.message, user_data, session_id)
        
        # Use updated_user_data if identification happened
        if updated_user_data:
            user_data = updated_user_data
            print(f"[LOGIN DEBUG] User identified: {user_data.get('naam')} (gradatie {user_data.get('gradatie')})")
        
        # 🎯 AUTO-FILL PROFIEL (Nieuw!)
        auto_fill_result = None
        if user_data and user_data.get("id"):
            # Check of auto-fill nodig is
            if PersonalInfoExtractor.should_auto_fill(user_data):
                # Get conversatie historie (simpel: laatste 50 berichten uit sessie)
                # Voor nu: gebruik huidige bericht, later: volledige history
                from datetime import datetime
                messages = [{
                    "content": message.message,
                    "isUser": True,
                    "timestamp": datetime.now().isoformat()
                }]
                
                # Auto-fill uit conversatie
                fill_result = PersonalInfoExtractor.auto_fill_profile(user_data, messages)
                
                if fill_result['updates']:
                    # Update user profile
                    for field, value in fill_result['updates'].items():
                        if field in ['naam', 'volledige_naam']:
                            user_data[field] = value
                        else:
                            if 'persoonlijke_info' not in user_data:
                                user_data['persoonlijke_info'] = {}
                            user_data['persoonlijke_info'][field] = value
                    
                    # Save updated profile
                    DataManager.update_user(user_data)
                    
                    # Prepare result voor frontend notificatie
                    auto_fill_result = {
                        'updated_fields': fill_result['metadata']['updated_fields'],
                        'updates': fill_result['updates']
                    }
        
        # 🎯 PERSON DETECTION: Detect new persons in message
        if user_data and user_data.get("id"):
            try:
                detected_persons = PersonDetectionService.detect_new_persons(
                    text=message.message,
                    user_id=user_data["id"],
                    require_context=True
                )
                
                if detected_persons:
                    # Store first suggestion as pending
                    first_person = detected_persons[0]
                    pending_person_suggestions[session_id] = first_person
                    
                    # Add suggestion to response
                    suggestion_text = f"\n\n---\n\n💡 **Nieuwe persoon gedetecteerd:** {first_person['naam']}"
                    if first_person.get('suggested_relatie'):
                        suggestion_text += f" (mogelijk je {first_person['suggested_relatie']})"
                    suggestion_text += f"\n\nWil je een Person Card aanmaken voor {first_person['naam']}? (ja/nee)"
                    
                    response_text += suggestion_text
            except Exception as e:
                print(f"[PERSON DETECTION ERROR] {e}")
        
        # 🎯 FORMAT RESPONSE: Apply intent-based formatting
        response_text = format_response(response_text, session_id)
        
        # Prepare response
        response_user_id = user_data.get("id") if user_data else None
        response_gradatie = user_data.get("gradatie") if user_data else None
        response_context = user_data if user_data else None
        
        print(f"[RESPONSE DEBUG] Returning: user_id={response_user_id}, gradatie={response_gradatie}, has_context={bool(response_context)}")
        
        return ChatResponse(
            response=response_text,
            user_id=response_user_id,
            user_gradatie=response_gradatie,
            context=response_context,
            auto_fill=auto_fill_result  # Nieuw veld!
        )
    except Exception as e:
        import traceback
        print(f"[CHAT ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/users")
async def get_all_users():
    """
    Get all users (admin only - for Status tab)
    Returns full user list with details
    """
    try:
        users = DataManager.load_users()
        # Return users without sensitive data
        safe_users = []
        for user in users:
            safe_users.append({
                "id": user.get("id"),
                "naam": user.get("naam"),
                "volledige_naam": user.get("volledige_naam"),
                "gradatie": user.get("gradatie"),
                "rol": user.get("rol"),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            })
        return {"users": safe_users, "total": len(safe_users)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system/status")
async def system_status():
    """
    Get system status
    """
    users = DataManager.load_users()
    knowledge = DataManager.load_knowledge()
    
    return {
        "status": "operational",
        "health": 98,
        "users_count": len(users),
        "knowledge_count": len(knowledge),
        "version": "1.0"
    }

@router.get("/knowledge")
async def get_knowledge():
    """
    Get knowledge base
    """
    from services.knowledge_service import KnowledgeService
    knowledge = KnowledgeService.get_all_knowledge()
    return {"knowledge": knowledge, "count": len(knowledge)}



@router.get("/knowledge/all")
async def get_all_knowledge():
    """
    Get all knowledge entries (admin only - TODO: add auth check)
    Sorted alphabetically by term
    """
    knowledge_data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    entries = knowledge_data.get("knowledge_entries", [])
    
    # Sort alfabetisch op 'term' field
    sorted_entries = sorted(entries, key=lambda x: (x.get("term") or "").lower())
    
    return {
        "entries": sorted_entries,
        "total": len(sorted_entries),
        "metadata": knowledge_data.get("metadata", {}),
        "sorted": True  # Indicator dat lijst gesorteerd is
    }

@router.get("/logs/{log_type}")
async def get_logs(log_type: str, limit: int = 50):
    """
    Get logs (admin only)
    log_type: nieuwe_mensen, verwijderde_mensen, nieuwe_woorden, etc.
    """
    from pathlib import Path
    
    log_file = Path(__file__).parent.parent / "data" / "logs" / f"{log_type}.log"
    
    if not log_file.exists():
        return {"logs": [], "count": 0}
    
    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Return last N lines
    return {"logs": lines[-limit:], "count": len(lines)}

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, sleutelwoord: str):
    """
    Delete user (with backup)
    """
    success = AuthService.delete_user(user_id, sleutelwoord)
    
    if success:
        return {"message": "Gebruiker verwijderd", "backup_created": True}
    else:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden of sleutelwoord incorrect")

@router.post("/gradatie/update")
async def update_gradatie(user_id: str, new_gradatie: int, reden: str):
    """
    Update user gradatie (admin only)
    """
    try:
        AuthService.update_gradatie(user_id, new_gradatie, reden, handmatig=True)
        return {"message": "Gradatie geüpdatet", "new_gradatie": new_gradatie}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/{user_id}")
async def get_user_analytics(user_id: str):
    """
    Get analytics for user
    """
    from services.conversation_service import ConversationService
    conv_service = ConversationService()
    
    analytics = conv_service.get_user_analytics(user_id)
    
    if not analytics:
        return {"message": "No analytics yet", "analytics": {}}
    
    return {"analytics": analytics}

@router.get("/conversations/{user_id}")
async def get_user_conversations(user_id: str, limit: int = 50):
    """
    Get recent conversations for user
    """
    from services.conversation_service import ConversationService
    conv_service = ConversationService()
    
    conversations = conv_service.get_user_conversations(user_id, limit)
    
    return {"conversations": conversations, "count": len(conversations)}

@router.get("/feedback")
async def get_feedback(status: Optional[str] = None):
    """
    Get feedback items
    Optional filter: poor, ok, good
    """
    from services.feedback_service import FeedbackService
    
    items = FeedbackService.get_all_feedback(filter_status=status)
    stats = FeedbackService.get_stats()
    
    return {
        "feedback_items": items,
        "count": len(items),
        "stats": stats
    }

@router.post("/feedback/{feedback_id}/improve")
async def improve_feedback(feedback_id: str, improved_answer: str, user_id: str):
    """
    Improve a feedback item with better answer
    """
    from services.feedback_service import FeedbackService
    
    result = FeedbackService.improve_answer(feedback_id, improved_answer, user_id)
    return result

@router.post("/feedback/{feedback_id}/teach")
async def teach_spark_feedback(feedback_id: str):
    """
    Teach Spark the improved answer
    """
    from services.feedback_service import FeedbackService
    
    result = FeedbackService.teach_spark(feedback_id)
    return result

@router.post("/session/heartbeat")
async def session_heartbeat(user_id: str):
    """
    Session heartbeat - updates last_active timestamp
    Call this every 30 seconds from frontend to keep session alive
    """
    try:
        result = AuthService.heartbeat(user_id)
        
        if result["status"] == "invalid":
            raise HTTPException(status_code=401, detail=result["message"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base")
async def get_full_knowledge_base():
    """Return volledige knowledge base (incl triggers array)"""
    try:
        import json
        from pathlib import Path
        
        kb_path = Path("/app/backend/data/learned_knowledge/knowledge_base.json")
        with open(kb_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {
            "knowledge_entries": [],
            "triggers": [],
            "total_entries": 0,
            "error": str(e)
        }
