from typing import Dict, Optional, Tuple
from services.nlp_service import NLPService
from services.knowledge_service import KnowledgeService
from services.knowledge_service_v2 import KnowledgeServiceV2
from services.knowledge_fallback_service import KnowledgeFallbackService
from services.event_extraction_service import EventExtractionService
from services.agenda_service import AgendaService
from services.layered_answer_service import LayeredAnswerService
from services.conversation_context_manager import ConversationContextManager
from services.conversation_state_manager import ConversationStateManager
from services.personal_sharing_detector import PersonalSharingDetector
from services.diary_service import DiaryService
from services.auth_service import AuthService
from services.system_health import SystemHealth
from services.conversation_service import ConversationService
from services.context_engine import ContextEngine
from services.pattern_detection_service import PatternDetectionService
from services.notes_service import NotesService
from services.graph_traversal_service import GraphTraversalService
from services.emotion_service import EmotionService
from services.conversation_cache_service import ConversationCacheService
from services.content_engine import ContentEngine
from services.context_layer import ContextLayer
from services.response_enhancer import get_response_enhancer
from services.profile_service import ProfileService
from services.emotion_detection_service import EmotionDetectionService
from services.trigger_manager_service import TriggerManagerService
from services.contextual_emotion_tracker import ContextualEmotionTracker
from services.emotion_stats import EmotionStats
from utils.data_manager import DataManager
from services.query_priority_handler import QueryPriorityHandler
from utils.logger import SparkLogger
from services.chat_action_handler import ChatActionHandler
import random

class SparkBrain:
    def __init__(self):
        self.nlp = NLPService()
        self.conversation_service = ConversationService()
        self.conversation_state = ConversationStateManager()
        self.cache_service = ConversationCacheService()
        self.content_engine = ContentEngine()
        self.context_layer = ContextLayer()
        self.response_enhancer = get_response_enhancer()
        self.spark_identity = DataManager.load_json("base_knowledge/spark_identity.json")
        self.spark_bijbel = DataManager.load_json("personality/spark_bijbel.json")
        self.spark_your_life = DataManager.load_json("base_knowledge/spark_your_life.json")
        self.roadkill = DataManager.load_json("base_knowledge/roadkill_community.json")
    
    def _enhance_response(
        self,
        response: str,
        contextual_analysis: Optional,
        user_data: Optional[Dict]
    ) -> str:
        """
        Enhance response using contextual analysis.
        
        Args:
            response: Base response
            contextual_analysis: ContextualAnalysis from Context Layer
            user_data: User data
        
        Returns:
            Enhanced response
        """
        if not contextual_analysis:
            return response
        
        try:
            # Get user name
            user_name = user_data.get('naam') if user_data else None
            
            # Enhance response
            enhanced = self.response_enhancer.enhance(
                base_response=response,
                contextual_analysis=contextual_analysis,
                user_name=user_name
            )
            
            # Apply word limit (from emotion system)
            word_limit = EmotionService.get_word_limit()
            enhanced = self.response_enhancer.add_word_limit_truncation(
                enhanced,
                word_limit
            )
            
            return enhanced
            
        except Exception as e:
            print(f"[ENHANCEMENT ERROR] {str(e)}")
            # Return original response if enhancement fails
            return response
    
    def _cache_message(self, message: str, sender: str, user_data: Optional[Dict], session_id: str, content_analysis=None):
        """
        Cache bericht voor snelle conversation context ophalen.
        
        Args:
            message: Message text
            sender: 'user' of 'spark'
            user_data: User data dict (optioneel)
            session_id: Session identifier
            content_analysis: ContentAnalysis object (optioneel, for richer metadata)
        """
        if not user_data:
            return
        
        # Extract context voor cache
        emotion = None
        topics = []
        sentiment = None
        intent = None
        
        # If we have ContentAnalysis, use it (much richer!)
        if content_analysis:
            topics = content_analysis.keywords.topics
            sentiment = content_analysis.sentiment
            intent = content_analysis.intent.primary_intent
            # Could also store: tone, compliments, etc.
        elif sender == "user":
            # Fallback: analyse user message voor cache metadata
            try:
                patterns = PatternDetectionService.analyze_message(message, user_data)
                topics = patterns.get('topics', [])
                sentiment = patterns.get('emotional_tone', 'neutraal')
                
                # Check voor commands
                command = self.nlp.detect_command(message)
                if command:
                    intent = command[0]
            except:
                pass  # Best effort - als analyse faalt, cache zonder metadata
        
        # Add to cache
        self.cache_service.add_message(
            session_id=session_id,
            message=message,
            sender=sender,
            user_id=user_data["id"],
            emotion=emotion,
            topics=topics,
            sentiment=sentiment,
            intent=intent
        )
    
    def _truncate_response_to_word_limit(self, response: str) -> str:
        """
        Truncate response op basis van huidige emotie woordlimiet
        
        Args:
            response: De originele response
            
        Returns:
            Getruncate response als het de limiet overschrijdt
        """
        word_limit = EmotionService.get_word_limit()
        words = response.split()
        
        if len(words) <= word_limit:
            return response
        
        # Truncate en voeg indicatie toe
        truncated = ' '.join(words[:word_limit])
        return truncated + "..."
    
    

    def _check_spam(self, message: str, user_data: Dict, session_id: str) -> Optional[str]:
        """
        Simpele spam detectie: 3x exact hetzelfde bericht = spam
        Returns: waarschuwing tekst als spam, None als ok
        """
        from datetime import datetime, timedelta
        
        user_id = user_data.get("id")
        
        # Check of user tijdelijk geblokkeerd is
        spam_blocked_until = user_data.get("spam_blocked_until")
        if spam_blocked_until:
            try:
                blocked_until = datetime.fromisoformat(spam_blocked_until)
                if datetime.utcnow() < blocked_until:
                    remaining = (blocked_until - datetime.utcnow()).seconds // 60
                    return f"🚫 Oeps! Je bent nog {remaining} minuut(en) in time-out. Neem even rust. ☕"
            except Exception:
                pass
        
        # Haal laatste 5 berichten op
        recent_messages = self.cache_service.get_recent_messages(user_id, session_id, limit=5)
        if not recent_messages or len(recent_messages) < 2:
            return None
        
        # Tel hoe vaak dit exacte bericht voorkomt in laatste berichten
        message_lower = message.lower().strip()
        duplicate_count = 0
        
        for cached_msg in recent_messages:
            if isinstance(cached_msg, dict):
                cached_text = cached_msg.get("message", "")
            else:
                cached_text = str(cached_msg)
            
            if cached_text.lower().strip() == message_lower:
                duplicate_count += 1
        
        # Als 3x of meer: spam!
        if duplicate_count >= 3:
            # Blokkeer tijdelijk (2 minuten)
            users = DataManager.load_users()
            for user in users:
                if user["id"] == user_id:
                    blocked_until = datetime.utcnow() + timedelta(minutes=2)
                    user["spam_blocked_until"] = blocked_until.isoformat()
                    DataManager.save_users(users)
                    break
            
            responses = [
                "🔄 Ik denk dat je vastloopt 😄 Neem even pauze!\n\nJe zit tijdelijk in time-out (2 minuten). ☕",
                "🤖 Hmmm... volgens mij herhaal je jezelf een beetje 😅\n\nEven 2 minuutjes relaxen? ⏰",
                "🌀 Je draait in een rondje! 🎵 \n\nIk geef je 2 minuten om weer scherp te komen. 💪"
            ]
            import random
            return random.choice(responses)
        
        return None

    def process_message(self, message: str, user_data: Optional[Dict] = None, session_id: Optional[str] = None) -> Tuple[str, Optional[Dict]]:
        """
        Main processing function for incoming messages
        Returns: (response_text, updated_user_data)
        """
        # Store session_id for context tracking
        self.current_session_id = session_id or (user_data.get("id") if user_data else "anonymous")
        
        # Reset snap guard at start of new message processing
        self._snap_already_checked = False
        
        # 🛡️ SPAM DETECTIE (simpel: 3x exact hetzelfde = spam)
        if user_data:
            spam_response = self._check_spam(message, user_data, self.current_session_id)
            if spam_response:
                return spam_response, user_data
        
        # 🧠 LAYER 1: Content Analysis (What is said)
        # Analyze message with Content Engine for intent, tone, topics, etc.
        content_analysis = None
        contextual_analysis = None
        
        if user_data:
            try:
                content_analysis = self.content_engine.analyze(
                    text=message,
                    user_data=user_data
                )
                # Store for later use (fallback, proactive suggestions)
                self._last_content_analysis = content_analysis
                
                # Log analysis for debugging (optional)
                print(f"[CONTENT] Intent: {content_analysis.intent.primary_intent}, "
                      f"Tone: {content_analysis.tone}, "
                      f"Topics: {content_analysis.keywords.topics[:2]}")
                
                # 🧠 LAYER 2: Context Analysis (What it means)
                contextual_analysis = self.context_layer.enrich(
                    content_analysis=content_analysis,
                    user_data=user_data,
                    session_id=self.current_session_id
                )
                # Store for greeting check
                self._last_contextual_analysis = contextual_analysis
                
                # Log context for debugging
                print(f"[CONTEXT] Phase: {contextual_analysis.conversation_phase}, "
                      f"Style: {contextual_analysis.suggested_response_style}, "
                      f"Continuation: {contextual_analysis.is_topic_continuation}")
                
                # 🧠 LAYER 2B: Event Extraction (detect events from conversation)
                detected_events = EventExtractionService.extract_events(message)
                if detected_events and user_data:
                    print(f"[EVENTS] Detected {len(detected_events)} event(s): {[e.title for e in detected_events]}")
                    # Store in pending agenda items
                    for event in detected_events:
                        AgendaService.add_pending_agenda_item(user_data["id"], event)
                    
                    # Store detected events for later feedback
                    self._detected_events = detected_events
                
            except Exception as e:
                print(f"[ANALYSIS ERROR] {str(e)}")
                # Continue without analysis if it fails
        
        # 🧠 LAYER 2C: Emotion Detection (NIEUWE PRIORITEIT)
        # Detecteer emoties VOOR knowledge lookup zodat we empathisch kunnen reageren
        emotion_detection = None
        contextual_emotion = None
        try:
            emotion_detection = EmotionDetectionService.detect_emotion(message)
            if emotion_detection:
                emotion_name = emotion_detection.get("emotion")
                intensity = emotion_detection.get("intensity")
                score = emotion_detection.get("score")
                print(f"[EMOTION] Detected: {emotion_name} (score: {score}, intensity: {intensity})")
                
                # Store for later use
                self._detected_emotion = emotion_detection
                
                # 🧠 NEW: Contextual Emotion Tracking
                # Link emotion to topics/knowledge cards for pattern analysis
                if user_data:
                    try:
                        contextual_emotion = ContextualEmotionTracker.detect_emotion_with_context(
                            text=message,
                            user_id=user_data.get("id")
                        )
                        
                        if contextual_emotion:
                            # Log contextual emotion
                            topics_str = ", ".join([t['topic'] for t in contextual_emotion.get('topics', [])[:2]])
                            general_str = ", ".join(contextual_emotion.get('general_topics', [])[:2])
                            print(f"[CONTEXTUAL EMOTION] {contextual_emotion['emotion']} + topics: {topics_str or general_str} (score: {contextual_emotion['final_score']})")
                            
                            # Save to emotion_stats for pattern analysis
                            EmotionStats.add_emotion_event(
                                user_id=user_data["id"],
                                emotion=contextual_emotion['emotion'],
                                word=contextual_emotion.get('word', ''),
                                base_score=contextual_emotion.get('base_score', 0),
                                final_score=contextual_emotion['final_score'],
                                intensifier=contextual_emotion.get('intensifier'),
                                multiplier=contextual_emotion.get('multiplier', 1.0),
                                context=contextual_emotion.get('context', message[:100]),
                                topics=contextual_emotion.get('topics', []),
                                general_topics=contextual_emotion.get('general_topics', [])
                            )
                            
                            # Store full contextual data for this session
                            self._contextual_emotion = contextual_emotion
                            
                    except Exception as e:
                        print(f"[CONTEXTUAL EMOTION ERROR] {str(e)}")
                        
        except Exception as e:
            print(f"[EMOTION ERROR] {str(e)}")
        
        # 🧠 Get user context (profile + notities + patterns)
        context = None
        if user_data:
            context = ContextEngine.get_user_context(user_data["id"], message)
            
            # Auto-create note if important pattern detected
            if ContextEngine.should_create_note(context):
                note_data = PatternDetectionService.create_insight_note(
                    context["patterns"],
                    user_data.get("naam", "User")
                )
                if note_data:
                    try:
                        NotesService.add_note(**note_data)
                        print(f"[AUTO-NOTE] Created note: {note_data['titel']}")
                    except Exception as e:
                        print(f"[AUTO-NOTE ERROR] {str(e)}")
        
        # Update user activity if logged in
        if user_data:
            # 🎉 FIRST MESSAGE WELCOME - Check VOOR update (gesprekken_count == 0)
            current_count = user_data.get("gesprekken_count", 0)
            is_first_message = (current_count == 0)
            
            # Nu update (dit increment gesprekken_count)
            AuthService.update_user_activity(user_data["id"])
            
            # Als dit het eerste bericht was, show welcome
            if is_first_message:
                welcome_response = self._get_first_message_welcome(user_data)
                if welcome_response:
                    return welcome_response, user_data
            
            # Session bonus: +5 trust bij langere sessie (5+ berichten)
            session_id = user_data.get("id")
            session_messages = self.cache_service.get_recent_messages(session_id, session_id, limit=10)
            if session_messages and len(session_messages) >= 5:
                # Langere sessie: extra trust bonus (alleen bij 5e bericht)
                if len(session_messages) == 5:
                    users = DataManager.load_users()
                    for user in users:
                        if user["id"] == user_data["id"]:
                            current_trust = user.get("trust_score", 0)
                            user["trust_score"] = min(current_trust + 5, 100)
                            DataManager.save_users(users)
                            break
            
            # Check inactivity reset (7 days → neutral emotion)
            EmotionService.check_inactivity_reset(user_data["id"])
            
            # Check for auto gradatie growth
            new_gradatie = AuthService.check_auto_gradatie_growth(user_data)
            if new_gradatie:
                AuthService.update_gradatie(
                    user_data["id"],
                    new_gradatie,
                    f"{user_data['gesprekken_count']}+ gesprekken",
                    handmatig=False
                )
        
        # 10% chance to add spontaneous status update (if logged in)
        should_add_status = random.random() < 0.15 and user_data is not None
        
        # 🔄 NEW: Check if greeting (AFTER context analysis, so we can check conversation_phase)
        if self.nlp.is_greeting(message):
            should_greet = True
            
            # Check if recent activity (mid-conversation = don't greet again)
            if hasattr(self, '_last_contextual_analysis') and self._last_contextual_analysis:
                # If phase is not "opening", we're mid-conversation
                if self._last_contextual_analysis.conversation_phase != "opening":
                    should_greet = False
            
            if should_greet:
                response = self._handle_greeting(user_data)
                if should_add_status:
                    response += f"\n\n{SystemHealth.get_random_status_message()}"
                
                # Log conversation
                if user_data:
                    self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                    
                    # Cache messages
                    session_id = getattr(self, 'current_session_id', user_data.get("id"))
                    self._cache_message(message, "user", user_data, session_id)
                    self._cache_message(response, "spark", user_data, session_id)
                
                return response, user_data
            # Else: continue to normal processing (don't intercept with greeting)
        
        # Try to extract identification ONLY if user is NOT already logged in
        # This prevents "Ik ben blij" from triggering login when user is in conversation
        if not user_data:
            identification = self.nlp.extract_identification(message)
            if identification:
                response, new_user_data = self._handle_identification(identification)
                # Add status after login sometimes
                if new_user_data and random.random() < 0.3:
                    status_msg = SystemHealth.get_random_status_message()
                    response += f"\n\n{status_msg}"
                
                # Log conversation
                if new_user_data:
                    self.conversation_service.log_conversation(
                        new_user_data["id"],
                        message,
                        response,
                        new_user_data
                    )
                    
                    # Cache messages voor snelle context access
                    self._cache_message(message, "user", new_user_data, self.current_session_id, content_analysis)
                    self._cache_message(response, "spark", new_user_data, self.current_session_id)
                
                # Enhance response before returning
                response = self._enhance_response(response, contextual_analysis, new_user_data)
                
                return response, new_user_data
        
        # 🧠 NEW: Check for disambiguation selection FIRST (before any other processing)
        # This allows users to respond to disambiguation prompts with any message type
        session_id = getattr(self, 'current_session_id', user_data.get("id") if user_data else "anonymous")
        disambiguation_ctx = ConversationContextManager.get_disambiguation_context(session_id)
        if disambiguation_ctx:
            # User has pending disambiguation options - try to interpret their choice
            selected_entry = self._interpret_disambiguation_choice(message, disambiguation_ctx)
            
            if selected_entry:
                # Clear the disambiguation context
                ConversationContextManager.clear_disambiguation_context(session_id)
                
                # Get the full answer for the selected entry
                concept = selected_entry.get("begrip", "")
                layered_answer = LayeredAnswerService.get_layered_answer(concept, 1)
                
                if layered_answer:
                    # Track usage
                    knowledge_id = layered_answer.get("knowledge_id")
                    if knowledge_id:
                        KnowledgeServiceV2.increment_usage(knowledge_id)
                    
                    # Store context for follow-up questions
                    ConversationContextManager.set_knowledge_context(
                        session_id,
                        concept,
                        1
                    )
                    
                    # Format response
                    is_admin = user_data and user_data.get("gradatie", 7) == 1
                    formatted_response = LayeredAnswerService.format_layered_response(
                        layered_answer,
                        show_layer_info=is_admin
                    )
                    
                    # Add graph context
                    graph_context = GraphTraversalService.build_graph_context_for_spark(concept)
                    if graph_context:
                        formatted_response += f"\n\n{graph_context}"
                    
                    # Log conversation
                    if user_data:
                        self.conversation_service.log_conversation(user_data["id"], message, formatted_response, user_data)
                        
                        # Cache messages
                        self._cache_message(message, "user", user_data, session_id, content_analysis)
                        self._cache_message(formatted_response, "spark", user_data, session_id)
                    
                    return formatted_response, user_data
            
            # If no match found, clear context and continue with normal processing
            # (User might have changed their mind and asked something else)
            ConversationContextManager.clear_disambiguation_context(session_id)
        
        # 🧠 NEW: Check for TRIGGER EDITING state (admin only)
        # This must be BEFORE command detection so we can capture word input
        if user_data and user_data.get("gradatie", 7) == 1:
            # Check if user just used /triggers and is now selecting a list
            trigger_menu_active = self.conversation_state.get_state(user_data.get("id"), "triggers_menu_active")
            
            if trigger_menu_active:
                # User should be selecting a trigger list (a, b, c, d)
                message_lower = message.lower().strip()
                
                if len(message_lower) == 1 and message_lower in ["a", "b", "c", "d", "e", "f"]:
                    # Clear menu state
                    self.conversation_state.clear_state(user_data.get("id"), "triggers_menu_active")
                    
                    # Handle selection
                    list_key = message_lower
                    lists = TriggerManagerService.get_available_lists()
                    
                    if list_key not in lists:
                        response = f"❌ Ongeldige keuze: '{message_lower}'. Type /triggers om opnieuw te beginnen."
                    else:
                        list_info = lists[list_key]
                        
                        # Show current triggers
                        current_display = TriggerManagerService.format_triggers_display(list_key)
                        
                        # Store selected list in conversation state for next messages
                        self.conversation_state.set_state(
                            user_data.get("id"),
                            "triggers_list_selected",
                            list_key
                        )
                        
                        response = f"{current_display}\n\n"
                        response += "**Woorden toevoegen** 📝\n\n"
                        response += "Type de woorden die je wilt toevoegen (meerdere woorden gescheiden door komma).\n"
                        response += "Type 'klaar' als je klaar bent.\n\n"
                        response += "Bijvoorbeeld: `feest, vieren, party`"
                    
                    # Log conversation
                    self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                    self._cache_message(message, "user", user_data, session_id, content_analysis)
                    self._cache_message(response, "spark", user_data, session_id)
                    
                    return response, user_data
            
            # Check if user is currently editing a trigger list
            trigger_list_key = self.conversation_state.get_state(user_data.get("id"), "triggers_list_selected")
            
            if trigger_list_key:
                # Admin is in trigger editing mode
                message_lower = message.lower().strip()
                
                # Check if user wants to stop
                if message_lower in ["klaar", "stop", "cancel", "annuleer", "stoppen"]:
                    self.conversation_state.clear_state(user_data.get("id"), "triggers_list_selected")
                    response = "✅ Trigger lijst beheer gestopt.\n\nType /triggers om opnieuw te beginnen."
                    
                    # Log conversation
                    self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                    self._cache_message(message, "user", user_data, session_id, content_analysis)
                    self._cache_message(response, "spark", user_data, session_id)
                    
                    return response, user_data
                
                # Parse words from input
                # Support: "woord1, woord2, woord3" or "woord1\nwoord2\nwoord3"
                words = []
                
                # Try comma separated first
                if "," in message:
                    words = [w.strip() for w in message.split(",") if w.strip()]
                # Try newline separated
                elif "\n" in message:
                    words = [w.strip() for w in message.split("\n") if w.strip()]
                # Single word
                else:
                    words = [message.strip()]
                
                # Add words to trigger list
                success, result_msg = TriggerManagerService.add_words_to_trigger_list(
                    trigger_list_key,
                    words,
                    default_score=3
                )
                
                if success:
                    # Clear emotion detection cache so new triggers are picked up
                    EmotionDetectionService._learned_triggers_cache = None
                    
                    response = f"{result_msg}\n\n"
                    response += "Type meer woorden om door te gaan, of 'klaar' om te stoppen."
                else:
                    response = f"{result_msg}\n\nProbeer opnieuw of type 'klaar' om te stoppen."
                
                # Log conversation
                self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                self._cache_message(message, "user", user_data, session_id, content_analysis)
                self._cache_message(response, "spark", user_data, session_id)
                
                return response, user_data
        
        # Detect commands
        command = self.nlp.detect_command(message)
        if command:
            response = self._handle_command(command, user_data, message)
            if should_add_status and command[0] not in ["yes_response", "no_response"]:
                response += f"\n\n💫 {SystemHealth.get_random_status_message()}"
            
            # Log conversation
            if user_data:
                self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                
                # Cache messages
                session_id = getattr(self, 'current_session_id', user_data.get("id"))
                self._cache_message(message, "user", user_data, session_id, content_analysis)
                self._cache_message(response, "spark", user_data, session_id)
            
            return response, user_data
        
        # Check for "deeper" requests (like "meer") BEFORE checking if it's a question
        # This allows context-based follow-ups to work
        session_id = getattr(self, 'current_session_id', user_data.get("id") if user_data else "anonymous")
        if ConversationContextManager.is_deeper_request(message):
            context = ConversationContextManager.get_knowledge_context(session_id)
            
            if context:
                # User wants more info on previous topic - delegate to question handler
                response = self._handle_question(message, user_data)
                if should_add_status:
                    response += f"\n\n{SystemHealth.get_random_status_message()}"
                
                # Log conversation
                if user_data:
                    self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                    
                    # Cache messages
                    session_id = getattr(self, 'current_session_id', user_data.get("id"))
                    self._cache_message(message, "user", user_data, session_id)
                    self._cache_message(response, "spark", user_data, session_id)
                
                return response, user_data
        
        # (Greeting check moved to after context analysis)
        
        # 🧠 NEW: Check if this is an answer to Spark's last question
        session_id = getattr(self, 'current_session_id', user_data.get("id") if user_data else "anonymous")
        last_question = ConversationStateManager.get_last_question(session_id)
        
        if last_question:
            # User might be answering our previous question
            answer_response = self._handle_answer_to_question(message, last_question, user_data)
            if answer_response:
                # Clear the state after handling
                ConversationStateManager.clear_last_question(session_id)
                
                if should_add_status:
                    answer_response += f"\n\n{SystemHealth.get_random_status_message()}"
                
                # Log conversation
                if user_data:
                    self.conversation_service.log_conversation(user_data["id"], message, answer_response, user_data)
                    self._cache_message(message, "user", user_data, session_id, content_analysis)
                    self._cache_message(answer_response, "spark", user_data, session_id)
                
                return answer_response, user_data
        
        # 🧠 CHECK FOR SNAP (before personal sharing) - VOOR ALLE USERS (ook guests!)
        # Guests kunnen ook kennis toevoegen!
        # GUARD: Only check once per message
        try:
            snap_proposal = None
            if not getattr(self, '_snap_already_checked', False):
                snap_proposal = self._check_for_snap(message, user_data)
                self._snap_already_checked = True
            
            if snap_proposal:
                concept = snap_proposal.get('concept', message)
                is_sentence = snap_proposal.get('is_sentence', False)
                possible_duplicate = snap_proposal.get('possible_duplicate')
                
                # Determine user identifier (ingelogd of guest)
                if user_data:
                    user_naam = user_data.get("naam", "Unknown")
                    user_id = user_data.get("id")
                else:
                    # Guest user - gebruik session_id
                    session_id = getattr(self, 'current_session_id', 'anonymous')
                    user_naam = f"anonymous_{session_id[:8]}"
                    user_id = None
                
                # Check: WOORD met mogelijk duplicate?
                if not is_sentence and possible_duplicate:
                    # Sla op met confirmation flag
                    result = KnowledgeService.create_knowledge_snap(
                        concept=concept,
                        context=message,
                        user_naam=user_naam,
                        user_id=user_id,
                        is_sentence_snap=False,
                        needs_confirmation=True,
                        similar_to=possible_duplicate
                    )
                    
                    if result:
                        # Geef feedback: bevestiging nodig
                        existing_name = possible_duplicate.get('begrip')
                        existing_desc = possible_duplicate.get('laag1', 'Geen beschrijving')[:80]
                        snap_feedback = f"⚠️ '{concept}' lijkt op '{existing_name}' ({existing_desc}...)\n   Is dit hetzelfde? (Ik sla het op voor jouw review)\n\n"
                        self._snap_feedback = snap_feedback
                else:
                    # ZIN of nieuw WOORD - gewoon opslaan
                    result = KnowledgeService.create_knowledge_snap(
                        concept=concept,
                        context=message,
                        user_naam=user_naam,
                        user_id=user_id,
                        is_sentence_snap=is_sentence
                    )
                    
                    if result:
                        # Snap saved - continue with normal flow
                        if is_sentence:
                            snap_feedback = f"✓ Context opgeslagen: '{concept[:60]}...'\n\n"
                        else:
                            snap_feedback = f"✓ Nieuw woord opgeslagen: '{concept}'\n\n"
                        self._snap_feedback = snap_feedback
        except Exception:
            import traceback
            traceback.print_exc()
        
        # 🧠 NEW: Check for CHAT ACTIONS (Uitgaven/Inkomsten/Dagboek via chat)
        # This happens BEFORE personal sharing to catch explicit action intents
        if user_data:
            action_result = ChatActionHandler.handle_chat_action(message, user_data["id"])
            if action_result:
                success, action_response = action_result
                
                # Add snap feedback if it was created
                if hasattr(self, '_snap_feedback'):
                    action_response = self._snap_feedback + action_response
                    del self._snap_feedback
                
                # Log conversation
                self.conversation_service.log_conversation(user_data["id"], message, action_response, user_data)
                self._cache_message(message, "user", user_data, session_id, content_analysis)
                self._cache_message(action_response, "spark", user_data, session_id)
                
                return action_response, user_data
        
        # 🧠 NEW: Check for DYNAMIC QUESTION ANSWER
        # If user is responding to a dynamic profile question
        if user_data:
            from services.dynamic_question_generator import DynamicQuestionGenerator
            
            current_state = DynamicQuestionGenerator.get_current_state(user_data)
            
            if current_state == "waiting_answer":
                # User is answering our question
                response = DynamicQuestionGenerator.handle_answer(user_data, message)
                if response:
                    # Log and return
                    self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                    self._cache_message(message, "user", user_data, session_id, content_analysis)
                    self._cache_message(response, "spark", user_data, session_id)
                    return response, user_data
            
            elif current_state == "confirming":
                # User is confirming our understanding
                response = DynamicQuestionGenerator.handle_confirmation(user_data, message)
                if response:
                    self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                    self._cache_message(message, "user", user_data, session_id, content_analysis)
                    self._cache_message(response, "spark", user_data, session_id)
                    return response, user_data
        
        # 🧠 NEW: Check for personal sharing (hobbies, food, life events)
        if user_data:  # Only for logged-in users
            personal_sharing = PersonalSharingDetector.detect_any_sharing(message)
            if personal_sharing:
                response = self._handle_personal_sharing(personal_sharing, user_data, session_id)
                
                # Add snap feedback if it was created
                if hasattr(self, '_snap_feedback'):
                    response = self._snap_feedback + response
                    del self._snap_feedback
                
                if should_add_status:
                    response += f"\n\n{SystemHealth.get_random_status_message()}"
                
                # Log conversation
                self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                self._cache_message(message, "user", user_data, session_id, content_analysis)
                self._cache_message(response, "spark", user_data, session_id)
                
                return response, user_data
        
        # 🧠 EMOTION EMPATHIC RESPONSE (NIEUWE PRIORITEIT)
        # Als sterke emotie gedetecteerd: geef EERST empathische reactie
        # Dit gebeurt VOOR knowledge lookup!
        if emotion_detection and EmotionDetectionService.should_respond_empathically(emotion_detection):
            empathic_resp = emotion_detection.get("empathic_response")
            if empathic_resp:
                # Update Spark's emotie op basis van empathie
                user_emotion = emotion_detection.get("emotion")
                if user_emotion:
                    # Map user emotion to Spark's empathic state
                    emotion_map = {
                        'blij': ('happy', 'gelukkig', 0.7),  # Spark wordt blij mee
                        'boos': ('scared', 'bezorgd', 0.6),  # Spark is bezorgd
                        'bang': ('sad', 'meelevend', 0.8),   # Spark leeft mee
                        'bedroefd': ('sad', 'verdrietig', 0.9)  # Spark wordt verdrietig
                    }
                    
                    if user_emotion in emotion_map:
                        spark_state, spark_sub, intensity = emotion_map[user_emotion]
                        EmotionService.update_emotion(
                            state=spark_state,
                            sub_state=spark_sub,
                            intensity=intensity,
                            triggered_by=f"empathy:{user_emotion}",
                            duration_minutes=15  # Blijft 15 minuten
                        )
                
                # Voor admin: toon debug info
                if user_data and user_data.get("gradatie", 7) == 1:
                    debug_info = EmotionDetectionService.format_emotion_debug_info(emotion_detection)
                    response = f"{debug_info}\n\n{empathic_resp}"
                else:
                    response = empathic_resp
                
                # Log conversation
                if user_data:
                    self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                    self._cache_message(message, "user", user_data, session_id, content_analysis)
                    self._cache_message(response, "spark", user_data, session_id)
                
                # Enhance response
                response = self._enhance_response(response, contextual_analysis, user_data)
                
                return response, user_data
        
        # If emotion detected but not strong enough for empathic response,
        # add debug info for admin at the end of normal response
        admin_emotion_debug = None
        if emotion_detection and user_data and user_data.get("gradatie", 7) == 1:
            admin_emotion_debug = f"\n\n[EMOTIE] {EmotionDetectionService.format_emotion_debug_info(emotion_detection)}"
        
        # 🧠 NEW: Check for "how are you" questions
        if self.nlp.detect_how_are_you(message):
            # User is asking US how we are - respond but DON'T set state
            # (we only set state when WE ask the user)
            response = self._handle_user_asks_how_are_you(user_data)
            
            # 🔧 FIX: After answering, ask back and SET STATE
            session_id = getattr(self, 'current_session_id', user_data.get("id") if user_data else "anonymous")
            
            # Sometimes ask back (50% chance to create natural conversation)
            if random.random() < 0.5 and user_data:
                response += "\n\nEn met jou?"
                # NOW set state because WE asked
                ConversationStateManager.set_last_question(session_id, "how_are_you")
                print("[STATE] Set last_question after asking back to user")
            
            if should_add_status:
                response += f"\n\n{SystemHealth.get_random_status_message()}"
            
            # Log conversation
            if user_data:
                self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                
                # Cache messages
                session_id = getattr(self, 'current_session_id', user_data.get("id"))
                self._cache_message(message, "user", user_data, session_id, content_analysis)
                self._cache_message(response, "spark", user_data, session_id)
            
            return response, user_data
        
        # 🧠 NEW: Check for thanks/gratitude
        if self.nlp.detect_thanks(message):
            response = self._handle_thanks(user_data)
            if should_add_status:
                response += f"\n\n{SystemHealth.get_random_status_message()}"
            
            # Log conversation
            if user_data:
                self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                
                # Cache messages
                session_id = getattr(self, 'current_session_id', user_data.get("id"))
                self._cache_message(message, "user", user_data, session_id, content_analysis)
                self._cache_message(response, "spark", user_data, session_id)
            
            return response, user_data
        
        # 🧠 CHECK FOR SNAP (before question handling) - vragen zijn ook context!
        # Ook voor guests!
        # GUARD: Skip if already checked in this message
        try:
            snap_proposal = None
            if not getattr(self, '_snap_already_checked', False):
                snap_proposal = self._check_for_snap(message, user_data)
                self._snap_already_checked = True
            
            if snap_proposal:
                concept = snap_proposal.get('concept', message)
                is_sentence = snap_proposal.get('is_sentence', False)
                possible_duplicate = snap_proposal.get('possible_duplicate')
                
                # Determine user identifier
                if user_data:
                    user_naam = user_data.get("naam", "Unknown")
                    user_id = user_data.get("id")
                else:
                    session_id = getattr(self, 'current_session_id', 'anonymous')
                    user_naam = f"anonymous_{session_id[:8]}"
                    user_id = None
                
                # Check: WOORD met mogelijk duplicate?
                if not is_sentence and possible_duplicate:
                    result = KnowledgeService.create_knowledge_snap(
                        concept=concept,
                        context=message,
                        user_naam=user_naam,
                        user_id=user_id,
                        is_sentence_snap=False,
                        needs_confirmation=True,
                        similar_to=possible_duplicate
                    )
                    
                    snap_feedback = ""
                    if result:
                        existing_name = possible_duplicate.get('begrip')
                        snap_feedback = f"⚠️ '{concept}' lijkt op '{existing_name}' - opgeslagen voor review\n\n"
                    
                    # ALWAYS generate response (zelfs bij duplicate)
                    if self.nlp.is_question(message):
                        response = snap_feedback + self._handle_question(message, user_data)
                    else:
                        response = snap_feedback + self._handle_conversation(message, user_data)
                else:
                    # ZIN of nieuw WOORD
                    result = KnowledgeService.create_knowledge_snap(
                        concept=concept,
                        context=message,
                        user_naam=user_naam,
                        user_id=user_id,
                        is_sentence_snap=is_sentence
                    )
                    
                    snap_feedback = ""
                    if result:
                        if is_sentence:
                            snap_feedback = f"✓ Context opgeslagen: '{concept[:50]}...'\n\n"
                        else:
                            snap_feedback = f"✓ Nieuw woord opgeslagen: '{concept}'\n\n"
                    
                    # ALWAYS generate response (zelfs bij duplicate)
                    if self.nlp.is_question(message):
                        response = snap_feedback + self._handle_question(message, user_data)
                    else:
                        response = snap_feedback + self._handle_conversation(message, user_data)
                
                if should_add_status:
                    response += f"\n\n{SystemHealth.get_random_status_message()}"
                
                # Log conversation
                if user_data:
                    self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                    
                    # Cache messages
                    session_id = getattr(self, 'current_session_id', user_data.get("id"))
                    self._cache_message(message, "user", user_data, session_id, content_analysis)
                    self._cache_message(response, "spark", user_data, session_id)
                
                return response, user_data
        except Exception:
            import traceback
            traceback.print_exc()
        
        # Check if question
        if self.nlp.is_question(message):
            response = self._handle_question(message, user_data)
            if should_add_status:
                response += f"\n\n{SystemHealth.get_random_status_message()}"
            
            # Log conversation
            if user_data:
                self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
                
                # Cache messages
                session_id = getattr(self, 'current_session_id', user_data.get("id"))
                self._cache_message(message, "user", user_data, session_id, content_analysis)
                self._cache_message(response, "spark", user_data, session_id)
            
            return response, user_data
        
        # General conversation
        response = self._handle_conversation(message, user_data)
        
        # 🧠 NEW: Check if we detected events and should give feedback
        if hasattr(self, '_detected_events') and self._detected_events and user_data:
            event_feedback = self._create_event_feedback(self._detected_events)
            if event_feedback:
                response = event_feedback
            # Clear detected events after feedback
            self._detected_events = None
        
        # 🧠 NEW: Enhance response met context
        if context:
            try:
                response = ContextEngine.enhance_response(response, context)
            except Exception as e:
                print(f"[ENHANCE ERROR] {str(e)}")
        
        # Add snap feedback if it was created (BEFORE status message)
        if hasattr(self, '_snap_feedback'):
            response = self._snap_feedback + response
            del self._snap_feedback
        
        if should_add_status:
            response += f"\n\n{SystemHealth.get_random_status_message()}"
        
        # Apply word limit based on current emotion (will be reapplied in enhancement)
        # response = self._truncate_response_to_word_limit(response)
        
        # Enhance response with contextual analysis
        response = self._enhance_response(response, contextual_analysis, user_data)
        
        # Log conversation
        if user_data:
            self.conversation_service.log_conversation(user_data["id"], message, response, user_data)
            
            # Cache messages
            session_id = getattr(self, 'current_session_id', user_data.get("id"))
            self._cache_message(message, "user", user_data, session_id, content_analysis)
            self._cache_message(response, "spark", user_data, session_id)
        
        return response, user_data
    
    def _handle_identification(self, identification: Dict) -> Tuple[str, Optional[Dict]]:
        """
        Handle user identification (login/register)
        Returns: (response_text, user_data)
        
        BELANGRIJK: Vereist altijd voornaam + achternaam + sleutelwoord
        """
        naam = identification.get("naam")
        sleutelwoord = identification.get("sleutelwoord")
        masterkey = identification.get("masterkey")
        volledige_naam = identification.get("volledige_naam")
        
        # Check 1: Moet altijd een naam hebben
        if not naam:
            return "Sorry, ik kon je naam niet herkennen. Probeer: 'Ik ben [voornaam achternaam] en mijn sleutelwoord is [woord]'", None
        
        # Check 2: Als alleen voornaam gegeven (geen achternaam), vraag door
        if not volledige_naam or ' ' not in volledige_naam:
            # Alleen voornaam gegeven, geen achternaam
            response = f"Hoi {naam}! 👋\n\n"
            response += "Voor identificatie heb ik je volledige naam nodig.\n\n"
            response += "Wat is je achternaam?\n\n"
            response += "Bijvoorbeeld: 'Jansen' of 'de Vries'"
            return response, None
        
        # Try authentication FIRST (check if naam + sleutelwoord combo exists)
        # Voor authenticatie: gebruik volledige_naam als die bestaat, anders naam
        auth_naam = volledige_naam if volledige_naam else naam
        user, is_masterkey = AuthService.authenticate_user(auth_naam, sleutelwoord, masterkey)
        
        if user:
            # User found! Login successful
            if is_masterkey:
                # Masterkey login - admin mode
                users_data = DataManager.load_users()
                knowledge_data = DataManager.load_knowledge()
                
                response = f"👑 Welkom terug {user['naam']}!\n\n"
                response += "🔓 Masterkey geaccepteerd\n"
                response += f"📊 Gradatie: {user['gradatie']} (Beheerder)\n"
                response += "⚡ Admin functies actief\n\n"
                response += "💾 Systeem Status:\n"
                response += f"├─ Totaal gebruikers: {len(users_data)}\n"
                response += f"├─ Knowledge entries: {len(knowledge_data)}\n"
                response += "└─ Spark health: 98% ✅\n\n"
                response += "Wat wil je doen?"
                
                return response, user
            else:
                # Normal login - Keep it simple and natural
                response = f"Welkom terug, {user['naam']}! 😊\n"
                response += f"📊 Gradatie: {user['gradatie']}\n\n"
                response += "Hoe is het met je?"
                
                # Set state: we asked "how are you"
                session_id = user.get("id")
                ConversationStateManager.set_last_question(session_id, "how_are_you")
                
                return response, user
        
        # If masterkey was provided but failed
        if masterkey:
            return f"❌ Masterkey toegang geweigerd voor {naam}. Ongeldige masterkey of gebruiker niet gevonden.", None
        
        # User not found - NO AUTO-CREATE!
        if not sleutelwoord:
            # No password given yet
            response = f"Hallo {volledige_naam if volledige_naam else naam}! 👋\n\n"
            response += "Ik heb je niet herkend. Gebruik je volledige naam (voornaam + achternaam) en sleutelwoord om in te loggen.\n\n"
            response += "Bijvoorbeeld: 'Ik ben Lisa Jansen en mijn sleutelwoord is Bloem123'\n\n"
            response += "💡 *Als je nog geen account hebt, neem dan contact op met de beheerder.*"
            return response, None
        
        # Sleutelwoord given but user not found - NO AUTO-CREATE!
        response = f"❌ Account niet gevonden voor '{volledige_naam if volledige_naam else naam}' met dit sleutelwoord.\n\n"
        response += "Controleer je volledige naam (voornaam + achternaam) en sleutelwoord.\n\n"
        response += "💡 *Tip: Gebruik je volledige naam, bijvoorbeeld 'Lisa Jansen' of 'Maurice de Vries'*\n\n"
        response += "Als je nog geen account hebt, neem dan contact op met de beheerder."
        
        return response, None
    
    def _handle_greeting(self, user_data: Optional[Dict]) -> str:
        """
        Handle greetings - met DynamicQuestionGenerator check
        """
        if not user_data:
            return "Hoi! 👋 Ik ben Spark. Ken ik jou al?"
        
        # Check if we should generate a dynamic profile question
        from services.dynamic_question_generator import DynamicQuestionGenerator
        
        try:
            question_data = DynamicQuestionGenerator.generate_question(user_data)
            if question_data:
                # We have a dynamic question!
                greeting = random.choice([
                    f"Hoi {user_data['naam']}! 😊",
                    f"Hey {user_data['naam']}!",
                ])
                
                # Add the question
                return f"{greeting}\n\n{question_data['question']}"
        except Exception as e:
            print(f"[DYNAMIC QUESTION ERROR] {str(e)}")
        
        # Normal greeting
        greetings = [
            f"Hoi {user_data['naam']}! 😊",
            f"Hey {user_data['naam']}!",
            f"Goeie dag {user_data['naam']}! 👋"
        ]
        return random.choice(greetings)
    
    def _handle_user_asks_how_are_you(self, user_data: Optional[Dict]) -> str:
        """
        Handle when USER asks how Spark is doing (NEW)
        Note: We don't set state here because USER asked US
        Uses conversation_triggers.json for responses
        """
        responses = self.nlp.conversation_triggers.get("how_are_you", {}).get("responses", [])
        if responses:
            return random.choice(responses)
        # Fallback
        return "Goed! En met jou? 😊"
    
    def _handle_personal_sharing(self, sharing_info: Dict, user_data: Dict, session_id: str) -> str:
        """
        Handle personal information sharing (NEW)
        
        Args:
            sharing_info: Dict with type, value, follow_up, profile_field
            user_data: User data
            session_id: Session ID
            
        Returns:
            Response with acknowledgment + follow-up question
        """
        # Build response
        value = sharing_info['value']
        follow_up = sharing_info['follow_up']
        is_sensitive = sharing_info.get('sensitive', False)
        
        # Save to profile (add to pending for now, will be auto-saved later)
        field = sharing_info['profile_field']
        
        # For now, just acknowledge and ask follow-up
        # (Actual saving to profile will be implemented in next phase)
        
        if is_sensitive:
            # Life event - empathetic response
            response = follow_up  # Already contains empathy
        else:
            # Regular sharing - enthusiastic acknowledgment
            if sharing_info['type'] == 'hobby':
                response = f"Leuk dat je van {value} houdt! {follow_up}"
            elif sharing_info['type'] == 'food_preference':
                response = f"Lekker! {follow_up}"
            elif sharing_info['type'] == 'drink_preference':
                response = follow_up
            else:
                response = f"Interessant! {follow_up}"
        
        # Set state: we asked a follow-up question
        ConversationStateManager.set_last_question(session_id, f"followup_{sharing_info['type']}")
        
        # Mark that we're collecting profile info (for next answer)
        # Store in temporary state
        self._pending_profile_info = {
            "field": field,
            "main_value": value,
            "type": sharing_info['type']
        }
        
        return response
    
    def _create_event_feedback(self, detected_events: list) -> Optional[str]:
        """
        Create user feedback when event is detected (NEW)
        Simple confirmation without gradation logic
        
        Args:
            detected_events: List of DetectedEvent objects
            
        Returns:
            Feedback message or None
        """
        if not detected_events:
            return None
        
        # Take first event (if multiple detected, focus on primary)
        event = detected_events[0]
        
        # Build simple confirmation message
        response = "Ik heb iets genoteerd 📅\n"
        
        # Add event details
        if event.date_str and event.date_str != "binnenkort":
            response += f"{event.date_str.capitalize()}"
        else:
            response += "Binnenkort"
        
        # Add title
        response += f" – {event.title.lower()}"
        
        # Add friendly question
        response += ".\n\nWil je een reminder?"
        
        return response
    
    def _handle_thanks(self, user_data: Optional[Dict]) -> str:
        """
        Handle thank you messages (NEW)
        Uses conversation_triggers.json for responses
        """
        responses = self.nlp.conversation_triggers.get("thanks", {}).get("responses", [])
        if responses:
            return random.choice(responses)
        # Fallback
        return "Graag gedaan! 😊"
    
    def _handle_answer_to_question(self, message: str, last_question: str, user_data: Optional[Dict]) -> Optional[str]:
        """
        Handle user's answer to Spark's previous question (IMPROVED)
        Now matches keywords in longer sentences, not just exact short phrases
        
        Args:
            message: User's response
            last_question: Type of question Spark asked ("how_are_you", etc.)
            user_data: User data
            
        Returns:
            Response string or None if not recognized as answer
        """
        message_lower = message.lower().strip()
        
        # Split into words for better matching in longer sentences
        words = message_lower.split()
        
        if last_question == "how_are_you":
            # Check for positive answers
            positive_answers = ["goed", "prima", "ok", "oké", "okay", "top", "super", "geweldig", "uitstekend", "fijn", "lekker", "chill"]
            neutral_answers = ["gaat wel", "redelijk", "normaal", "gewoon", "kan beter", "zo zo", "mwah"]
            negative_answers = ["slecht", "niet goed", "beroerd", "rot", "kut", "waardeloos", "moe", "down", "verdrietig"]
            
            # Positive response (check if any positive word in sentence)
            if any(ans in words or ans in message_lower for ans in positive_answers):
                print(f"[ANSWER] Detected positive answer to 'how_are_you': {message[:50]}")
                return random.choice([
                    "Fijn om te horen! 😊",
                    "Mooi! 👍",
                    "Top! 🎉",
                    "Dat is goed om te horen!",
                    "Graag gedaan! 😊"
                ])
            
            # Neutral response (check phrases first, then words)
            elif any(ans in message_lower for ans in neutral_answers):
                print(f"[ANSWER] Detected neutral answer to 'how_are_you': {message[:50]}")
                return random.choice([
                    "Ah, begrijpelijk. Wil je erover praten?",
                    "Oké, kan ik ergens mee helpen?",
                    "Hmm, als je wilt praten, ben ik er."
                ])
            
            # Negative response
            elif any(ans in words or ans in message_lower for ans in negative_answers):
                print(f"[ANSWER] Detected negative answer to 'how_are_you': {message[:50]}")
                return random.choice([
                    "Dat spijt me om te horen. Wil je erover praten? 💙",
                    "Ah, vervelend. Ik luister als je wilt praten.",
                    "Balen. Kan ik je ergens mee helpen?"
                ])
        
        # Not recognized as an answer
        return None
    
    def _handle_command(self, command: Tuple[str, str], user_data: Optional[Dict], original_message: str = "") -> str:
        """
        Handle commands
        """
        cmd_type, content = command
        
        if cmd_type == "roadmap":
            # Show roadmap
            from services.roadmap_service import RoadmapService
            return RoadmapService.get_chat_summary()
        
        elif cmd_type == "show_users":
            # Show known users
            users_data = DataManager.load_users()
            response = f"👥 **Ik ken {len(users_data)} mensen:**\n\n"
            for u in users_data[:10]:  # Show max 10
                response += f"• {u['naam']} (Gradatie {u['gradatie']}) - {u.get('rol', 'Gebruiker')}\n"
            
            if len(users_data) > 10:
                response += f"\n... en nog {len(users_data) - 10} anderen!"
            
            return response
        
        elif cmd_type == "yes_response":
            # User wants to create account - ask for keyword
            if not user_data:
                response = "Geweldig! 🎉\n\n"
                response += "Geef me dan je sleutelwoord. Dit gebruik je later om weer in te loggen.\n\n"
                response += "Typ: **[jouw naam] [jouw sleutelwoord]**\n\n"
                response += "Bijvoorbeeld: 'Lisa Zonnebloem' of 'Jan Geheim123'"
                return response
            else:
                return "Je bent al ingelogd! 😊"
        
        elif cmd_type == "no_response":
            # User doesn't want account - temporary session
            if not user_data:
                response = "Geen probleem! 👍\n\n"
                response += "We kunnen gewoon chatten zonder dat ik dingen onthoud.\n"
                response += "Als je later toch een account wilt, typ dan gewoon:\n"
                response += "**'Ik ben [naam] en mijn sleutelwoord is [woord]'**\n\n"
                response += "Waar wil je over praten?"
                return response
            else:
                return "Je bent al ingelogd! Als je wilt uitloggen, typ 'afmelden'."
        
        elif cmd_type == "help":
            # Show help based on gradatie
            return self._get_help_text(user_data)
        
        elif cmd_type == "logout":
            # Logout user
            if not user_data:
                return "Je bent nog niet ingelogd."
            
            naam = user_data.get('naam', 'vriend')
            return f"👋 Tot ziens {naam}! Log opnieuw in wanneer je terug bent."
        
        elif cmd_type == "system_status":
            # Show system status
            from services.system_health import SystemHealth
            users = DataManager.load_users()
            knowledge = DataManager.load_json("learned_knowledge/knowledge_base.json")
            
            response = "⚙️ **Systeem Status**\n\n"
            response += "🟢 Status: Operationeel\n"
            response += "💚 Health: 100%\n"
            response += f"👥 Gebruikers: {len(users)}\n"
            response += f"🧠 Knowledge entries: {len(knowledge.get('knowledge_entries', []))}\n"
            response += "\n✅ Alle systemen draaien goed!"
            return response
        
        elif cmd_type == "say_command":
            # Admin only: Spark zegt wat je wilt
            if not user_data or user_data.get("gradatie", 7) != 1:
                return "⛔ Deze functie is alleen beschikbaar voor admins (gradatie 1)"
            
            # Spark herhaalt gewoon de tekst die je meegeeft
            message_to_say = content.strip()
            if not message_to_say:
                return "💬 Gebruik: 'Spark zeg eens: [jouw boodschap]'"
            
            return message_to_say
        
        elif cmd_type == "triggers_menu":
            # Admin only: Trigger lijst beheer
            if not user_data or user_data.get("gradatie", 7) != 1:
                return "⛔ Deze functie is alleen beschikbaar voor admins (gradatie 1)"
            
            # Set state so next message is interpreted as menu selection
            self.conversation_state.set_state(
                user_data.get("id"),
                "triggers_menu_active",
                True
            )
            
            return TriggerManagerService.get_list_menu_text()
        
        elif cmd_type == "triggers_view":
            # View trigger list (admin only)
            if not user_data or user_data.get("gradatie", 7) != 1:
                return "⛔ Deze functie is alleen beschikbaar voor admins (gradatie 1)"
            
            list_key = content.strip().lower()
            success, output = TriggerManagerService.view_trigger_list(list_key)
            
            if success:
                return output
            else:
                return f"❌ {output}\n\nGeldige opties: a (blij), b (boos), c (bang), d (bedroefd)"
        
        elif cmd_type == "triggers_move":
            # Move word between emotion lists (admin only)
            if not user_data or user_data.get("gradatie", 7) != 1:
                return "⛔ Deze functie is alleen beschikbaar voor admins (gradatie 1)"
            
            # Parse: /triggers move [woord] van [emotie1] naar [emotie2]
            import re
            match = re.search(r'move\s+(\w+)\s+van\s+([a-d])\s+naar\s+([a-d])', content.lower())
            
            if not match:
                return "❌ Formaat: `/triggers move [woord] van [a/b/c/d] naar [a/b/c/d]`"
            
            word = match.group(1)
            from_list = match.group(2)
            to_list = match.group(3)
            
            success, message = TriggerManagerService.move_word(word, from_list, to_list)
            
            # Clear emotion cache so changes take effect
            if success:
                EmotionDetectionService._learned_triggers_cache = None
            
            return message
        
        elif cmd_type == "triggers_remove":
            # Remove word from trigger list (admin only)
            if not user_data or user_data.get("gradatie", 7) != 1:
                return "⛔ Deze functie is alleen beschikbaar voor admins (gradatie 1)"
            
            # Parse: /triggers remove [woord] van [emotie]
            import re
            match = re.search(r'remove\s+(\w+)\s+van\s+([a-d])', content.lower())
            
            if not match:
                return "❌ Formaat: `/triggers remove [woord] van [a/b/c/d]`"
            
            word = match.group(1)
            list_key = match.group(2)
            
            success, message = TriggerManagerService.remove_word(word, list_key)
            
            # Clear emotion cache
            if success:
                EmotionDetectionService._learned_triggers_cache = None
            
            return message
        
        elif cmd_type == "achievement_celebration":
            # User telling us they unlocked an achievement - celebrate!
            from services.achievement_service import AchievementService
            from datetime import datetime, timedelta
            
            user_id = user_data.get("id") if user_data else None
            if not user_id:
                return "Wat leuk! Vertel me meer! 😊"
            
            progress = AchievementService.get_user_achievements(user_id)
            unlocked = progress.get("unlocked", [])
            
            if not unlocked:
                return "Ik zie nog geen achievements voor jou, maar ik kijk ernaar uit! 😊"
            
            # Get most recent achievement
            recent = sorted(unlocked, key=lambda a: a.get("unlocked_at", ""), reverse=True)[0]
            
            # Check if within last 24h
            unlocked_time = datetime.fromisoformat(recent["unlocked_at"])
            now = datetime.now()
            hours_ago = (now - unlocked_time).total_seconds() / 3600
            
            if hours_ago > 24:
                # Not recent, generic celebration
                response = f"Gefeliciteerd met je achievements! Je hebt er al {len(unlocked)} unlocked. 🎉"
            else:
                # Recent! Specific celebration
                response = f"🎉 **Gefeliciteerd met {recent['name']}!** {recent['icon']}\n\n"
                response += f"_{recent['description']}_\n\n"
                response += f"Je hebt nu **{progress['current_word_count']} woorden** geleerd. "
                response += "Dankjewel dat je me helpt groeien! 📚\n\n"
                response += f"**+{recent['xp_reward']} XP** verdiend!"
                
                # Show next milestone
                if progress.get("next_milestone"):
                    next_m = progress["next_milestone"]
                    response += f"\n\n🎯 Volgende: {next_m['icon']} **{next_m['name']}** ({next_m['remaining']} woorden te gaan)"
            
            return response
        
        elif cmd_type == "achievements":
            # Show user's achievement progress
            from services.achievement_service import AchievementService
            
            user_id = user_data.get("id") if user_data else None
            if not user_id:
                return "Je moet ingelogd zijn om achievements te bekijken."
            
            progress = AchievementService.get_user_achievements(user_id)
            
            response = "🏆 **Jouw Achievements**\n\n"
            response += f"📚 Woorden geleerd: **{progress['current_word_count']}**\n"
            response += f"🎯 Progress: **{progress['total_unlocked']}/{progress['total_achievements']}** ({progress['progress_percentage']}%)\n"
            response += f"⭐ Totaal XP: **{progress['total_xp_earned']}** XP\n\n"
            
            if progress['unlocked']:
                response += "✅ **Unlocked Achievements:**\n"
                for ach in sorted(progress['unlocked'], key=lambda a: a.get('milestone', 0)):
                    response += f"{ach['icon']} **{ach['name']}** (+{ach['xp_reward']} XP)\n"
                    response += f"   _{ach['description']}_\n"
            else:
                response += "Je hebt nog geen achievements unlocked.\n"
            
            if progress['next_milestone']:
                next_m = progress['next_milestone']
                response += "\n🎯 **Volgende Milestone:**\n"
                response += f"{next_m['icon']} **{next_m['name']}** ({next_m['milestone']} woorden)\n"
                response += f"_{next_m['description']}_\n"
                response += f"Progress: {next_m['current_progress']}/{next_m['milestone']} ({next_m['remaining']} remaining)\n"
                response += f"Reward: **+{next_m['xp_reward']} XP**"
            else:
                response += "\n🎉 **Je hebt alle achievements unlocked!**"
            
            return response
        
        elif cmd_type == "dagboek_entry":
            # Add dagboek entry via chat
            if not user_data:
                return "Je moet ingelogd zijn om dagboek entries toe te voegen."
            
            from services.dagboek_service import DagboekService
            
            # Try to detect mood from content
            mood = self._detect_mood_from_text(content)
            
            try:
                entry = DagboekService.add_entry(
                    user_id=user_data["id"],
                    content=content,
                    mood=mood
                )
                
                mood_emoji = {
                    "blij": "😊",
                    "verdrietig": "😢",
                    "boos": "😠",
                    "neutraal": "😐",
                    "enthousiast": "🤩"
                }.get(mood, "📝")
                
                response = f"✅ Dagboek entry opgeslagen! {mood_emoji}\n\n"
                if mood:
                    response += f"Mood gedetecteerd: {mood}\n"
                response += f"📊 {entry['word_count']} woorden"
                
                return response
            except Exception as e:
                return f"❌ Kon entry niet opslaan: {str(e)}"
        
        elif cmd_type == "agenda_event":
            # Add agenda event via chat
            if not user_data:
                return "Je moet ingelogd zijn om afspraken toe te voegen."
            
            from services.agenda_service import AgendaService
            import re
            from datetime import datetime, timedelta
            
            # Try to parse date from content
            # Patterns: "morgen 10:00", "25 december", "vrijdag 14:00"
            date_str = None
            tijd_str = None
            
            # Extract time if present
            time_match = re.search(r'(\d{1,2}):(\d{2})', content)
            if time_match:
                tijd_str = f"{time_match.group(1).zfill(2)}:{time_match.group(2)}"
                content = content.replace(time_match.group(0), '').strip()
            
            # Simple date parsing
            content_lower = content.lower()
        
        elif cmd_type == "bio_query":
            # Answer bio/identity questions
            query_type = content if content else "general"
            
            # 🧠 NEW: Check if there are multiple meanings in knowledge base first!
            if query_type and query_type not in ["general"]:
                from services.knowledge_service_v2 import KnowledgeServiceV2
                all_knowledge = KnowledgeServiceV2.get_ranked_knowledge()
                query_lower = query_type.lower()
                
                # Find matching entries
                exact_matches = [
                    k for k in all_knowledge 
                    if k.get("status") == "active" and 
                    query_lower in k.get("begrip", "").lower()
                ]
                
                # If multiple meanings exist, show disambiguation
                if len(exact_matches) > 1:
                    session_id = getattr(self, 'current_session_id', user_data.get("id") if user_data else "anonymous")
                    is_admin = user_data and user_data.get("gradatie", 7) == 1
                    
                    response = f"**{query_type.title()}** heeft meerdere betekenissen:\n\n"
                    
                    for idx, match in enumerate(exact_matches, 1):
                        begrip = match.get("begrip", "")
                        laag1 = match.get("lagen", {}).get("laag1", "")
                        if laag1:
                            preview = laag1[:80] + "..." if len(laag1) > 80 else laag1
                            
                            usage = match.get("usage_count", 0)
                            if usage > 10:
                                popularity = " 🔥"
                            elif usage > 5:
                                popularity = " ⭐"
                            else:
                                popularity = ""
                            
                            response += f"{idx}. **{begrip}**{popularity}\n   {preview}\n\n"
                    
                    if not is_admin:
                        response += "💡 Vraag specifieker voor meer details!"
                    
                    # Store disambiguation context
                    ConversationContextManager.set_disambiguation_context(
                        session_id,
                        query_type,
                        exact_matches
                    )
                    
                    return response
            
            # Original bio_query logic (fallback for hardcoded bios)
            if query_type == "roadkill" or query_type == "roadkill_community":
                bio = DataManager.load_json("knowledge/roadkill_bio.json")
                response = "🎮 **Over Roadkill**\n\n"
                response += f"{bio['content']['wie']}\n\n"
                response += f"**Filosofie:** {bio['content']['filosofie']}\n\n"
                
                if query_type == "roadkill_community":
                    response += f"**💜 Roadkill Community:**\n{bio['content']['roadkill_community']}\n\n"
                    response += f"**🛍️ Roadkill Shop:** {bio['content']['roadkill_shop']}\n\n"
                    response += f"**Impact:** {bio['content']['impact']}"
                else:
                    response += f"**Roadkill Community:** {bio['content']['roadkill_community']}\n\n"
                    response += f"💡 Waarden: {', '.join([w.split(':')[0] for w in bio['content']['waarden']])}"
                
                return response
            
            elif query_type == "spark_your_life":
                bio = DataManager.load_json("knowledge/spark_your_life_bio.json")
                response = "🌟 **Over Spark Your Life**\n\n"
                response += f"{bio['content']['wat_is_spark_your_life']}\n\n"
                response += f"**Missie:** {bio['content']['missie']}\n\n"
                response += f"**Visie:** {bio['content']['visie']}\n\n"
                response += f"🌱 {bio['content']['zorgboerderij']}"
                return response
            
            else:
                # General "wie ben je" about Spark itself
                response = "Ik ben **Spark**, een lerende AI gemaakt door Willem Spakman (Roadkill).\n\n"
                response += "🎯 **Mijn doel:** Leren van elk gesprek en jou helpen groeien. Ik ben niet alleen een chatbot - ik word jouw digitale partner die meeleert en meegroeit.\n\n"
                response += "🧠 Ik ben verbonden aan:\n"
                response += "• **Roadkill Community** - Een gaming community die mensen verbindt\n"
                response += "• **Spark Your Life** - Een zorgboerderij gericht op persoonlijke groei\n\n"
                response += "💡 Vraag me over 'Roadkill' of 'Spark Your Life' voor meer info!"
                return response

            now = datetime.now()
            
            if 'morgen' in content_lower:
                date_obj = now + timedelta(days=1)
                content = content_lower.replace('morgen', '').strip()
            elif 'overmorgen' in content_lower:
                date_obj = now + timedelta(days=2)
                content = content_lower.replace('overmorgen', '').strip()
            elif 'vandaag' in content_lower:
                date_obj = now
                content = content_lower.replace('vandaag', '').strip()
            else:
                # Default to today
                date_obj = now
            
            # Format datetime
            if tijd_str:
                date_str = f"{date_obj.strftime('%Y-%m-%d')}T{tijd_str}:00"
            else:
                date_str = f"{date_obj.strftime('%Y-%m-%d')}T12:00:00"
            
            try:
                event = AgendaService.add_event(
                    user_id=user_data["id"],
                    titel=content.strip(),
                    date=date_str,
                    beschrijving=None,
                    reminder=False
                )
                
                response = "✅ Afspraak toegevoegd! 📅\n\n"
                response += f"**{event['titel']}**\n"
                response += f"📆 {datetime.fromisoformat(date_str).strftime('%d %B %Y, %H:%M')}"
                
                return response
            except Exception as e:
                return f"❌ Kon afspraak niet opslaan: {str(e)}"
        
        elif cmd_type == "learn":
            # Learn something new
            if not user_data:
                return "Je moet ingelogd zijn om mij iets te leren."
            
            # Try to parse "X = Y" or "X is Y"
            if " is " in content:
                parts = content.split(" is ", 1)
                begrip = parts[0].strip()
                betekenis = parts[1].strip()
            elif " = " in content:
                parts = content.split(" = ", 1)
                begrip = parts[0].strip()
                betekenis = parts[1].strip()
            else:
                begrip = content
                betekenis = "Onthouden door " + user_data['naam']
            
            from models.knowledge import KnowledgeCreate
            new_knowledge = KnowledgeService.add_knowledge(KnowledgeCreate(
                begrip=begrip,
                betekenis=betekenis,
                bron=user_data['naam']
            ))
            
            # 🧠 AUTO-GRAPH: Push naar graph en detecteer relaties
            try:
                from services.graph_service import GraphService
                from services.relation_detection_service import RelationDetectionService
                
                node = GraphService.add_node(
                    titel=begrip,
                    content=betekenis,
                    node_type="knowledge",
                    source="conversation",
                    tags=[user_data['naam'].lower()],
                    metadata={'created_by_user_id': user_data.get('id')}
                )
                
                # Auto-detect relaties
                relations_count = RelationDetectionService.auto_detect_and_create_relations(node["id"])
                print(f"[GRAPH] Knowledge '{begrip}' → {relations_count} relaties gevonden")
            except Exception as e:
                print(f"[GRAPH ERROR] {str(e)}")
            
            return f"✅ Genoteerd! Ik heb geleerd: '{begrip}' = {betekenis}"
        
        elif cmd_type == "show":
            # Show knowledge
            results = KnowledgeService.search_knowledge(content)
            if results:
                response = f"📚 Dit weet ik over '{content}':\n\n"
                for r in results[:5]:
                    response += f"• {r['begrip']}: {r['betekenis']}\n"
                return response
            else:
                return f"🤔 Ik weet nog niets over '{content}'. Wil je het me leren?"
        
        elif cmd_type == "diary_entry":
            # Add diary entry
            if not user_data:
                return "Je moet ingelogd zijn om een dagboek bij te houden."
            
            from models.diary import DiaryCreate
            sentiment = self.nlp.detect_sentiment(content)
            
            DiaryService.add_diary_entry(
                user_data["id"],
                user_data["sleutelwoord"],
                DiaryCreate(content=content, mood=sentiment)
            )
            
            mood_emoji = {"positief": "😊", "negatief": "😔", "neutraal": "😌"}.get(sentiment, "📖")
            return f"📖 Dagboek entry opgeslagen! {mood_emoji}\n📅 {sentiment.capitalize()} stemming gedetecteerd"
        
        elif cmd_type == "show_diary":
            # Show diary
            if not user_data:
                return "Je moet ingelogd zijn om je dagboek te bekijken."
            
            entries = DiaryService.get_diary_entries(
                user_data["id"],
                user_data["sleutelwoord"],
                limit=5
            )
            
            if entries:
                response = "📖 Je recente dagboek entries:\n\n"
                for entry in entries:
                    mood = entry.get("mood", "neutraal")
                    mood_emoji = {"positief": "😊", "negatief": "😔", "neutraal": "😌"}.get(mood, "📖")
                    response += f"📅 {entry['date']} {mood_emoji}\n"
                    response += f"'{entry['content'][:100]}...'\n\n"
                return response
            else:
                return "📖 Je dagboek is nog leeg. Begin met: 'Spark, dagboek entry: [jouw tekst]'"
        
        elif cmd_type == "note":
            # Add a note/brainfart
            if not user_data:
                return "Je moet ingelogd zijn om notities toe te voegen."
            
            # Check if admin (gradatie 1 = Willem/admin)
            if user_data.get("gradatie", 7) != 1:
                return "🔒 Alleen admins kunnen notities toevoegen via chat. Gebruik het Notities tabblad."
            
            from services.notes_service import NotesService
            
            # Extract potential title (first 50 chars or until newline)
            titel = content.split('\n')[0][:50] if '\n' in content else content[:50]
            if len(content) > 50:
                titel += "..."
            
            try:
                note = NotesService.add_note(
                    titel=titel,
                    inhoud=content,
                    categorie="Algemeen",
                    created_by=user_data.get("naam", "Admin")
                )
                
                return f"📝 Notitie opgeslagen!\n\n**{note['titel']}**\n\nBekijk in het Notities tabblad."
            except Exception as e:
                return f"❌ Kon notitie niet opslaan: {str(e)}"
        
        elif cmd_type == "emotion":
            # Set emotion (admin only)
            if not user_data or user_data.get("gradatie", 7) != 1:
                return "🔒 Deze functie is alleen voor admins"
            
            emotion_cmd = content.strip()
            
            # Reset command
            if emotion_cmd in ["reset", "neutraal", "neutral", ""]:
                from services.emotion_service import EmotionService
                EmotionService.reset_to_neutral()
                return "😌 Emotie gereset naar neutral."
            
            # Set emotion command (format: "blij 30" voor 30 minuten)
            parts = emotion_cmd.split()
            emotion_name = parts[0] if parts else ""
            duration = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            
            # Map Nederlandse namen naar states
            emotion_map = {
                "blij": ("happy", "blijdschap"),
                "vrolijk": ("happy", "vreugde"),
                "euforie": ("happy", "euforie"),
                "euforisch": ("happy", "euforie"),
                "boos": ("angry", "irritatie"),
                "woede": ("angry", "woede"),
                "woedend": ("angry", "razernij"),
                "verdrietig": ("sad", "verdrietig"),
                "somber": ("sad", "somber"),
                "neerslachtig": ("sad", "neerslachtig"),
                "bang": ("scared", "angstig"),
                "voorzichtig": ("scared", "voorzichtig"),
                "paniek": ("scared", "paniek")
            }
            
            if emotion_name in emotion_map:
                from services.emotion_service import EmotionService
                state, sub_state = emotion_map[emotion_name]
                EmotionService.set_emotion(
                    state=state,
                    sub_state=sub_state,
                    intensity=0.7,
                    triggered_by=f"admin_command_{user_data.get('naam', 'unknown')}",
                    duration_minutes=duration
                )
                duration_msg = f" voor {duration} minuten" if duration else ""
                return f"😊 Emotie ingesteld op '{emotion_name}'{duration_msg}!"
            
            return f"❓ Onbekende emotie '{emotion_name}'.\n\n📝 Beschikbare emoties:\n• blij, vrolijk, euforie\n• boos, woede\n• verdrietig, somber\n• bang, voorzichtig, paniek\n• reset (terug naar neutral)\n\n💡 Gebruik: emotie: [naam] [minuten]"
        
        return "Ik begrijp dat commando nog niet helemaal. Kun je het anders formuleren?"
    
    def _handle_question(self, message: str, user_data: Optional[Dict]) -> str:
        """
        Handle questions
        """
        message_lower = message.lower()
        
        # Use session_id (works for both logged-in and anonymous users)
        session_id = getattr(self, 'current_session_id', user_data.get("id") if user_data else "anonymous")
        
        # Questions about Spark
        if any(w in message_lower for w in ["wie ben je", "wat ben je", "wie ben jij"]):
            return self._introduce_spark()
        
        # "Wie ben ik?" - context aware
        if any(w in message_lower for w in ["wie ben ik", "wat is mijn naam"]):
            if user_data:
                willem_data = DataManager.load_json("base_knowledge/willem_profile.json")
                if user_data["naam"] == "Willem Spakman" or user_data["naam"] == "Willem":
                    response = "Je bent Willem Spakman, mijn maker en bedenker! 💙\n\n"
                    response += "Gamertag: Roadkill\n"
                    response += "Jouw bedrijven: Spark Your Life, Roadkill Community\n"
                    response += "Jouw dochter: Lotus (de belangrijkste persoon in je leven)\n\n"
                    response += "Je hebt mij gemaakt als jouw digitale nalatenschap."
                    return response
                else:
                    return f"Je bent {user_data['naam']}, gradatie {user_data['gradatie']} ({user_data['rol']})"
            else:
                return "Ik weet niet wie je bent. Stel jezelf voor met je naam en sleutelwoord!"
        
        # Questions about Lotus
        if "lotus" in message_lower:
            willem_data = DataManager.load_json("base_knowledge/willem_profile.json")
            lotus_info = willem_data.get("relaties", {}).get("dochter", {})
            if user_data and (user_data["naam"] == "Willem Spakman" or user_data["naam"] == "Willem"):
                response = "Lotus (Lotus Martens) is jouw dochter, Willem. ❤️\n\n"
                response += "Ze is de belangrijkste persoon in je leven.\n\n"
                response += "Je hebt mij gemaakt zodat Lotus altijd met 'papa' kan praten, ook als je er niet meer bent."
            else:
                response = "Lotus Martens is de dochter van Willem Spakman.\n"
                response += "Ze is heel belangrijk voor hem."
            return response
        
        # Questions about Willem
        if "willem" in message_lower:
            willem_data = DataManager.load_json("base_knowledge/willem_profile.json")
            response = "Willem Spakman (gamertag: Roadkill) is mijn maker en bedenker.\n\n"
            response += "Hij is de oprichter van Spark Your Life en de Roadkill Community.\n"
            response += f"Zijn filosofie: {willem_data.get('filosofie', {}).get('kernwaarde', '')}.\n\n"
            response += "Hij heeft me gemaakt om mensen te helpen groeien en ontwikkelen."
            return response
        
        # Questions about Spark Your Life
        if "spark your life" in message_lower:
            missie = self.spark_your_life.get("missie", "")
            response = "Spark Your Life is een coaching en begeleiding onderneming.\n\n"
            response += f"Missie: {missie}\n\n"
            response += "Kernwaarden: "
            for kw in self.spark_your_life.get("kernwaarden", [])[:3]:
                response += f"{kw['naam']}, "
            return response.rstrip(", ")
        
        # Use session_id for context tracking
        session_id = getattr(self, 'current_session_id', user_data.get("id") if user_data else "anonymous")
        
        # Check if user wants to go deeper on current topic
        if ConversationContextManager.is_deeper_request(message):
            context = ConversationContextManager.get_knowledge_context(session_id)
            
            if context:
                # User wants more info on previous topic
                concept = context.get("concept")
                new_layer = ConversationContextManager.increment_layer(session_id)
                
                if new_layer:
                    # Get deeper layer
                    layered_answer = LayeredAnswerService.get_layered_answer(concept, new_layer)
                    
                    if layered_answer:
                        # 📊 Track usage for deeper layers too (V2)
                        knowledge_id = layered_answer.get("knowledge_id")
                        if knowledge_id:
                            KnowledgeServiceV2.increment_usage(knowledge_id)
                        
                        is_admin = user_data and user_data.get("gradatie", 7) == 1
                        formatted_response = LayeredAnswerService.format_layered_response(
                            layered_answer,
                            show_layer_info=is_admin
                        )
                        return formatted_response
                else:
                    return f"Dit was al de diepste laag over {concept}. Wil je iets anders weten?"
            else:
                # No context found - ask user to be more specific
                return "Ik weet niet waar je meer over wilt weten. Stel een nieuwe vraag! 😊"
        
        # Detect if user wants deeper layer from start
        requested_layer = LayeredAnswerService.detect_layer_request(message)
        if not requested_layer:
            requested_layer = 1  # Default to layer 1
        
        # Try to find concept in message
        concept = self._extract_concept(message)
        
        if concept:
            # 🧠 NEW: Check for disambiguation (multiple meanings)
            all_knowledge = KnowledgeServiceV2.get_ranked_knowledge()  # ← Use V2 with ranking!
            concept_lower = concept.lower()
            
            # Find all entries that match this concept (case-insensitive partial match)
            exact_matches = [
                k for k in all_knowledge 
                if k.get("status") == "active" and 
                concept_lower in k.get("begrip", "").lower()
            ]
            
            # Already sorted by rank_score from get_ranked_knowledge()!
            
            if len(exact_matches) > 1:
                # Multiple meanings! Already sorted by rank_score
                is_admin = user_data and user_data.get("gradatie", 7) == 1
                
                response = f"**{concept.title()}** heeft meerdere betekenissen:\n\n"
                
                # Show ALL matches (no limit!)
                for idx, match in enumerate(exact_matches, 1):
                    begrip = match.get("begrip", "")
                    laag1 = match.get("lagen", {}).get("laag1", "")
                    if laag1:
                        # Show first 80 chars as preview
                        preview = laag1[:80] + "..." if len(laag1) > 80 else laag1
                        
                        # Show popularity indicator for top matches
                        usage = match.get("usage_count", 0)
                        if usage > 10:
                            popularity = " 🔥"  # Hot
                        elif usage > 5:
                            popularity = " ⭐"  # Popular
                        else:
                            popularity = ""
                        
                        response += f"{idx}. **{begrip}**{popularity}\n   {preview}\n\n"
                
                if not is_admin:
                    response += "💡 Vraag specifieker voor meer details!"
                
                # 🧠 NEW: Store disambiguation options for follow-up
                ConversationContextManager.set_disambiguation_context(
                    session_id,
                    concept,
                    exact_matches  # Store full entries with IDs
                )
                
                return response
            
            # 🧠 Get graph context BEFORE answering
            graph_context = GraphTraversalService.build_graph_context_for_spark(message)
            
            # Get layered answer
            layered_answer = LayeredAnswerService.get_layered_answer(concept, requested_layer)
            
            if layered_answer:
                # 📊 Track usage automatically with V2
                knowledge_id = layered_answer.get("knowledge_id")
                if knowledge_id:
                    KnowledgeServiceV2.increment_usage(knowledge_id)
                
                # Store context for follow-up questions (use session_id)
                ConversationContextManager.set_knowledge_context(
                    session_id,
                    concept,
                    requested_layer
                )
                
                # Format response (show_layer_info = False for regular users, True for admin)
                is_admin = user_data and user_data.get("gradatie", 7) == 1
                formatted_response = LayeredAnswerService.format_layered_response(
                    layered_answer,
                    show_layer_info=is_admin
                )
                
                # 🧠 Add graph context if available
                if graph_context:
                    formatted_response += f"\n\n{graph_context}"
                
                return formatted_response
        
        # Fallback: Try old search method
        results = KnowledgeService.search_knowledge(message)
        if results:
            # 🧠 NEW: Get graph context
            graph_context = GraphTraversalService.build_graph_context_for_spark(message)
            
            # Handle both old and new format
            if 'betekenis' in results[0]:
                response = f"💡 {results[0]['betekenis']}"
            elif 'lagen' in results[0]:
                # Use layer 1 from new format
                laag1 = results[0]['lagen'].get('laag1', '')
                if laag1:
                    response = f"💡 {laag1}"
                else:
                    response = ""
            
            # Add graph context if available
            if response and graph_context:
                response += f"\n\n{graph_context}"
            
            if response:
                return response
        
        # 🧠 NEW: Try graceful fallback (step back to general definition)
        # Extract potential concepts from the question using detected topics
        # Only try this if we have content_analysis available
        try:
            if hasattr(self, '_last_content_analysis') and self._last_content_analysis and self._last_content_analysis.keywords.topics:
                for topic in self._last_content_analysis.keywords.topics[:2]:  # Check top 2 topics
                    fallback_response = KnowledgeFallbackService.create_fallback_response(
                        query=message,
                        detected_concept=topic
                    )
                    if fallback_response:
                        return fallback_response
        except:
            pass  # Fallback failed, continue to normal "don't know"
        
        # 🧠 NEW: Proactive knowledge suggestions based on detected topics
        # If we detected topics but couldn't answer, maybe we have knowledge about those topics
        try:
            if hasattr(self, '_last_content_analysis') and self._last_content_analysis and self._last_content_analysis.keywords.topics:
                for topic in self._last_content_analysis.keywords.topics[:2]:
                    # Check if this topic exists in knowledge base
                    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
                    entries = data.get("knowledge_entries", [])
                    
                    for entry in entries:
                        if entry.get("status") == "active" and topic.lower() in entry.get("begrip", "").lower():
                            # We have knowledge about this topic!
                            return f"Ik kon je vraag niet precies beantwoorden, maar ik weet wel iets over **{topic}**. Wil je daar meer over weten?"
        except:
            pass  # Proactive suggestion failed, continue
        
        # 🧠 NEW: Check norms and values availability (only for admin)
        if user_data and user_data.get("gradatie", 7) == 1:
            has_nv, nv_message = GraphTraversalService.check_norms_and_values_availability()
            if nv_message:
                # Return the "don't know" message WITH the norms/values suggestion
                base_response = "Dat is een goede vraag! Ik weet het antwoord nog niet. Deze vraag heb ik opgeslagen zodat Willem (de admin) hem kan beantwoorden."
                return base_response + nv_message
        
        # Spark doesn't know - create an unanswered question entry for admin
        if user_data:
            KnowledgeService.create_unanswered_question(
                question=message,
                asked_by=user_data.get("naam", "Onbekend")
            )
        
        return "Dat is een goede vraag! Ik weet het antwoord nog niet. Deze vraag heb ik opgeslagen zodat Willem (de admin) hem kan beantwoorden."
    
    def _extract_concept(self, message: str) -> Optional[str]:
        """
        Extract the main concept from a question
        Examples:
            "wat is een appel" -> "appel"
            "vertel over Bitcoin" -> "Bitcoin"
            "leg uit wat auto is" -> "auto"
        """
        import re
        message_lower = message.lower()
        
        # Patterns to match
        patterns = [
            r"wat is (?:een |de |het )?([a-zA-Z0-9]+)",
            r"vertel (?:over|mij over) ([a-zA-Z0-9]+)",
            r"leg uit wat ([a-zA-Z0-9]+)",
            r"uitleg over ([a-zA-Z0-9]+)",
            r"wat weet je over ([a-zA-Z0-9]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                return match.group(1)
        
        return None
    
    def _handle_conversation(self, message: str, user_data: Optional[Dict]) -> str:
        """
        Handle general conversation with behavior rules
        """
        from services.spark_response_generator import SparkResponseGenerator
        from services.response_behavior import ResponseBehavior, MessageType
        
        session_id = self.current_session_id or "default"
        sentiment = self.nlp.detect_sentiment(message)
        
        # Detect message type
        message_type, confidence = ResponseBehavior.detect_message_type(message)
        
        # 🧠 Match with existing knowledge cards FIRST
        card_match = self._match_with_knowledge_cards(message)
        if card_match:
            # Generate response from matched card
            response = self._generate_response_from_card(card_match, message)
            return response
        
        # 🧠 Check if this could be a snap (context statement) - AUTO SAVE
        # GUARD: Skip if already checked in this message
        snap_proposal = None
        if user_data and not getattr(self, '_snap_already_checked', False):
            try:
                snap_proposal = self._check_for_snap(message, user_data)
                self._snap_already_checked = True
            except Exception:
                import traceback
                traceback.print_exc()
        
        # If snap detected, AUTO CREATE card (no confirmation needed)
        if snap_proposal:
            concept = snap_proposal.get('concept', message)
            user_naam = user_data.get("naam", "Unknown")
            
            try:
                result = KnowledgeService.create_knowledge_snap(
                    concept=concept,
                    context=message,
                    user_naam=user_naam,
                    is_sentence_snap=True  # Skip meaningful check for context zinnen
                )
                
                if result:
                    # Short feedback - snap saved
                    return f"✓ Snap opgeslagen: '{concept}'"
                else:
                    # Failed to create (probably duplicate)
                    pass  # Continue with fallback
            except Exception as e:
                import sys
                print(f"[SNAP] Error creating snap: {e}", file=sys.stderr)
                # Continue with fallback
        
        # 🧠 FALLBACK: Use Response Generator + Behavior Rules
        try:
            result = SparkResponseGenerator.generate_response(
                query=message,
                context={"tags": [], "sentiment": sentiment}
            )
            
            # Use generator response
            content = result.get("response", "")
            
            # Format according to behavior rules
            response = ResponseBehavior.format_response(
                message_type=message_type,
                content=content,
                card_context=None
            )
            
            # If empty, use sentiment-based fallback
            if not response:
                if sentiment == "negatief":
                    return "Ik luister."
                elif sentiment == "positief":
                    return "Vertel me meer."
                else:
                    return "Vertel me meer."
            
            return response
            
        except Exception as e:
            print(f"[FALLBACK ERROR] {e}")
            # Final fallback based on type
            rules = ResponseBehavior.get_behavior_rules(message_type)
            import random
            return random.choice(rules["templates"]) if rules["templates"] else "Vertel me meer."
    
    def _match_with_knowledge_cards(self, message: str) -> Optional[Dict]:
        """
        Match user input with existing knowledge cards
        Uses fuzzy matching + intent triggers for better recognition
        
        Returns matched card or None
        """
        import sys
        from difflib import SequenceMatcher
        from services.intent_triggers import IntentTriggers
        
        message_lower = message.lower()
        
        # Load knowledge base
        data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = data.get("knowledge_entries", [])
        
        # Detect intents from triggers (for synonym matching)
        detected_intents = IntentTriggers.detect_intent(message, min_score=1)
        
        # Fuzzy matching with scoring
        best_match = None
        best_score = 0
        
        for entry in entries:
            score = 0
            
            # Only consider active cards with laag1
            has_laag1 = entry.get("lagen", {}).get("laag1")
            if not has_laag1:
                continue
            
            # 1. Check begrip (fuzzy similarity + meervoud handling)
            begrip = entry.get("begrip", "").lower()
            if begrip:
                import re
                
                # Exact WHOLE WORD match (highest priority)
                begrip_pattern = r'\b' + re.escape(begrip) + r'\b'
                
                # Check direct match first
                if re.search(begrip_pattern, message_lower):
                    score += 10
                else:
                    # Try plural normalization: check if any word in message
                    # is a plural of begrip
                    message_words = message_lower.split()
                    matched_plural = False
                    
                    for word in message_words:
                        # Remove common plural suffixes and check
                        if word.endswith('en') and len(word) > 4:
                            # "taken" → "tak" or "taak"
                            singular1 = word[:-2]  # "tak"
                            singular2 = word[:-2] + 'k'  # "taak"
                            if begrip in [singular1, singular2]:
                                score += 10
                                matched_plural = True
                                break
                        elif word.endswith('s') and len(word) > 4:
                            # "algoritmes" → "algoritme"
                            singular = word[:-1]
                            if begrip == singular:
                                score += 10
                                matched_plural = True
                                break
                    
                    # If no plural match, try fuzzy
                    if not matched_plural:
                        # Fuzzy similarity (threshold: 0.75 for quality matches)
                        similarity = SequenceMatcher(None, begrip, message_lower).ratio()
                        if similarity > 0.75:
                            score += int(similarity * 8)  # Max 8 points
            
            # 2. Check tags (strong signal)
            tags = entry.get("tags", [])
            for tag in tags:
                if tag.lower() in message_lower:
                    score += 3
            
            # 3. Word overlap (partial match)
            begrip_words = set(begrip.split())
            message_words = set(message_lower.split())
            common_words = begrip_words & message_words
            if common_words:
                score += len(common_words) * 2
            
            # 4. NEW: Intent-based matching (synoniemen via triggers)
            # Als card tags matchen met detected intents, verhoog score
            for intent, intent_score in detected_intents:
                if intent in tags:
                    score += intent_score * 2  # Bonus voor intent match
                    print(f"[INTENT MATCH] '{intent}' detected in message, matches card tag", file=sys.stderr)
            
            # 5. NEW: Check if begrip matches any trigger words
            for intent, intent_score in detected_intents:
                triggers = IntentTriggers.get_triggers_for_intent(intent)
                if begrip in triggers or any(trigger in begrip for trigger in triggers):
                    score += 3  # Synoniem match via triggers
                    print(f"[SYNONYM MATCH] '{begrip}' matches triggers for '{intent}'", file=sys.stderr)
            
            if score > best_score:
                best_score = score
                best_match = entry
        
        # Threshold: 6 points for confident matches (balanced)
        if best_score >= 6:
            print(f"[CARD MATCH] Matched '{message}' with '{best_match['begrip']}' (score: {best_score})", file=sys.stderr)
            return best_match
        
        return None
    
    def _generate_response_from_card(self, card: Dict, user_message: str) -> str:
        """
        Generate response - INTENT FIRST, then card content
        Intent bepaalt hoe we reageren, card geeft context
        """
        from services.spark_response_generator import SparkResponseGenerator
        from services.response_behavior import ResponseBehavior, MessageType
        
        begrip = card.get("begrip", "")
        laag1 = card.get("lagen", {}).get("laag1", "")
        tags = card.get("tags", [])
        
        # PRIORITEIT 1: Detect message type (intent)
        message_type, confidence = ResponseBehavior.detect_message_type(user_message)
        
        # PRIORITEIT 2: Bepaal gedrag op basis van type
        # ACTION/STATUS → kort bevestigend (GEEN definitie)
        # QUESTION → informatief (WEL definitie)
        
        if message_type == MessageType.ACTION:
            # Actie-zin → bevestig actie, niet uitleggen wat het is
            # "ik moet een uitgave registreren" → "Genoteerd."
            rules = ResponseBehavior.get_behavior_rules(MessageType.ACTION)
            import random
            
            # 70% kort, 30% met vraag
            if random.random() < 0.7:
                return random.choice(rules["templates"])
            else:
                # Actie-response met vraag
                action_responses = [
                    "Begrepen. Zal ik dit vastleggen?",
                    "Genoteerd. Moet ik dit registreren?",
                    "Duidelijk. Zal ik dit verwerken?"
                ]
                return random.choice(action_responses)
        
        elif message_type == MessageType.STATUS:
            # Status update → bevestig, optioneel vraag
            rules = ResponseBehavior.get_behavior_rules(MessageType.STATUS)
            import random
            
            if random.random() < 0.5:
                return random.choice(rules["templates"])
            else:
                return f"{random.choice(rules['templates'])} Zal ik dit verwerken?"
        
        elif message_type == MessageType.EMOTION:
            # Emotie → kort empathisch (gebruik laag1 als beschikbaar)
            if laag1 and len(laag1) < 50:
                return laag1
            else:
                rules = ResponseBehavior.get_behavior_rules(MessageType.EMOTION)
                import random
                return random.choice(rules["templates"])
        
        elif message_type == MessageType.QUESTION:
            # VRAAG → informatief (gebruik laag1)
            # "wat is een uitgave" → "Een uitgave is..."
            return laag1 if laag1 else "Ik weet hier nog geen antwoord op."
        
        else:
            # UNKNOWN → gebruik laag1 of fallback
            return laag1 if laag1 else "Vertel me meer."
    
    def _check_for_snap(self, message: str, user_data: Dict) -> Optional[Dict]:
        """
        Check if message could be a snap, but DON'T create it yet.
        
        WOORDEN (1-2 woorden): duplicate check + bevestiging
        ZINNEN (3+ woorden): skip alleen bij EXACT match, kleine variaties WEL opslaan
        
        Returns: {
            'concept': 'extracted concept', 
            'original': 'original message',
            'is_sentence': bool,
            'possible_duplicate': Dict or None
        } or None
        """
        import sys
        from config.dutch_stopwords import extract_concept_from_input
        
        # Skip very short meaningless messages
        if len(message) < 3 or message.lower() in ["ja", "nee", "ok", "hoi", "dag", "hey", "dank", "thanks"]:
            return None
        
        # Determine: WOORD of ZIN? (check dit VOOR extract)
        words = message.split()
        is_sentence = len(words) >= 3
        
        # Load existing entries voor duplicate check
        data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = data.get("knowledge_entries", [])
        
        if is_sentence:
            # 📝 ZIN (context) - gebruik VOLLEDIGE zin, geen extraction
            snap_concept = message.strip()
            snap_normalized = snap_concept.lower().strip()
            
            # Check voor EXACT dezelfde zin (case-insensitive)
            exact_match = [e for e in entries 
                          if snap_normalized == e.get("begrip", "").lower().strip()]
            
            if exact_match:
                # Duplicate detected - maar laat door voor Spark's leerproces
                # Later zal Spark vragen: "Bedoel je X?" en op basis van antwoord beslissen
                print(f"[SNAP CHECK] ⚠️ ZIN possible duplicate: '{snap_concept}' - creating for review", file=sys.stderr)
                # Return proposal zodat snap wordt aangemaakt (Spark leert nog)
                return {
                    'concept': snap_concept,
                    'original': message,
                    'is_sentence': True,
                    'possible_duplicate': None
                }
            else:
                print(f"[SNAP CHECK] ✓ ZIN (context): '{snap_concept}' - nieuwe context", file=sys.stderr)
                return {
                    'concept': snap_concept,
                    'original': message,
                    'is_sentence': True,
                    'possible_duplicate': None
                }
        else:
            # 🔤 WOORD (concept) - extract en check duplicates
            extracted = extract_concept_from_input(message)
            if not extracted:
                return None  # Geen concept te extracten
            
            snap_concept = extracted
            snap_lower = snap_concept.lower().strip()
            
            # Check for similar existing entries
            exact_match = [e for e in entries 
                          if snap_lower == e.get("begrip", "").lower().strip()]
            
            if exact_match:
                # Found possible duplicate - return met confirmation needed
                print(f"[SNAP CHECK] ⚠️ WOORD mogelijk duplicate: '{snap_concept}' - bevestiging nodig", file=sys.stderr)
                return {
                    'concept': snap_concept,
                    'original': message,
                    'is_sentence': False,
                    'possible_duplicate': {
                        'begrip': exact_match[0].get('begrip'),
                        'laag1': exact_match[0].get('lagen', {}).get('laag1', 'Geen beschrijving')[:100]
                    }
                }
            else:
                # New concept
                print(f"[SNAP CHECK] ✓ WOORD (nieuw): '{snap_concept}'", file=sys.stderr)
                return {
                    'concept': snap_concept,
                    'original': message,
                    'is_sentence': False,
                    'possible_duplicate': None
                }
    
    def _create_knowledge_snaps_from_message(self, message: str, user_data: Dict):
        """
        Extract important concepts from a message and create knowledge snaps for unknown ones.
        
        Now intelligently extracts concepts from questions and statements,
        delegating extraction + normalization to create_knowledge_snap.
        """
        import re
        import sys
        
        print(f"[SNAP DEBUG] Called with message: {message[:50]}", file=sys.stderr)
        
        # Skip very short messages UNLESS they look like important concepts
        # Allow single words that might be knowledge queries
        words = message.split()
        if len(words) < 2:
            # Check if it's a potential knowledge query (single meaningful word)
            if len(message) < 3 or message.lower() in ["ja", "nee", "ok", "hoi", "dag", "hey"]:
                print("[SNAP DEBUG] Message too short or not meaningful, skipping", file=sys.stderr)
                return
            # Single word 3+ chars → might be knowledge query, allow it
            print(f"[SNAP DEBUG] Single word '{message}' - treating as potential knowledge query", file=sys.stderr)
        
        # STRATEGY: Send the entire message to create_knowledge_snap
        # Let it handle extraction, normalization, and filtering
        # This supports both questions ("Wat is liefde?") and statements ("vertel over blockchain")
        
        try:
            result = KnowledgeService.create_knowledge_snap(
                concept=message,  # Send full message, not just single words
                context=message,
                user_naam=user_data.get("naam", "Unknown")
            )
            if result:
                extracted_concept = result.get("begrip", "?")
                print(f"[KNOWLEDGE SNAP] ✅ Created: '{extracted_concept}' from message by {user_data.get('naam')}", file=sys.stderr)
            else:
                print("[SNAP DEBUG] Message rejected by filters", file=sys.stderr)
        except Exception as e:
            print(f"[KNOWLEDGE SNAP ERROR] {str(e)}", file=sys.stderr)
    
    def _interpret_disambiguation_choice(self, message: str, disambiguation_ctx: Dict) -> Optional[Dict]:
        """
        Interpret user's choice from disambiguation options
        
        Handles:
        - Numeric choices: "1", "2", "nummer 2"
        - Text references: "de gamer", "track", "community"
        
        Returns:
        - Selected knowledge entry dict, or None if no match
        """
        message_lower = message.lower().strip()
        options = disambiguation_ctx.get("options", [])
        
        if not options:
            return None
        
        # Try numeric selection first
        import re
        
        # Match "1", "nummer 1", "optie 2", etc.
        number_match = re.search(r'\b(\d+)\b', message_lower)
        if number_match:
            choice_num = int(number_match.group(1))
            if 1 <= choice_num <= len(options):
                return options[choice_num - 1]
        
        # Try text-based matching: find keywords in the begrip of each option
        # Example: "vertel me meer over de gamer" should match "Roadkill - Track voor gamers"
        for option in options:
            begrip = option.get("begrip", "").lower()
            
            # Check for significant word overlap
            # Extract meaningful words from user message (skip common words)
            stop_words = {"vertel", "me", "meer", "over", "de", "het", "een", "wat", "is", "van", "voor", "mij"}
            user_words = set(message_lower.split()) - stop_words
            
            # Check if any user word appears in the begrip
            for word in user_words:
                if len(word) > 3 and word in begrip:  # Only match words > 3 chars
                    return option
        
        # No match found
        return None
    
    def _introduce_spark(self) -> str:
        """
        Introduce Spark
        """

    def _get_first_message_welcome(self, user_data: Dict) -> Optional[str]:
        """
        Get welcome message for first-time users (gesprekken_count == 1)
        Uses trigger system: welcome_grad_{gradatie}
        
        Returns: welcome response or None (continue normal flow)
        """
        gradatie = user_data.get("gradatie", 7)
        user_naam = user_data.get("naam", "vriend")
        
        # Try to fetch welcome trigger from knowledge base
        trigger_begrip = f"welcome_grad_{gradatie}"
        
        try:
            # Load knowledge base
            kb_data = DataManager.load_knowledge()
            
            # Search for welcome trigger
            for card in kb_data.get('knowledge_entries', []):
                if card.get('begrip') == trigger_begrip:
                    # Found welcome trigger!
                    response_config = card.get('response', {})
                    variants = response_config.get('variants', [])
                    
                    if variants:
                        import random
                        welcome_text = random.choice(variants)
                        # Replace {naam} placeholder
                        welcome_text = welcome_text.replace('{naam}', user_naam)
                        
                        print(f"[FIRST_MSG] ✅ Using trigger: {trigger_begrip}")
                        return welcome_text
            
            print(f"[FIRST_MSG] ⚠️ Trigger '{trigger_begrip}' not found, using fallback")
            
        except Exception as e:
            print(f"[FIRST_MSG] ❌ Error loading trigger: {e}")
        
        # FALLBACK: Simple welcome based on gradatie
        fallback_welcomes = {
            1: f"👑 Welkom {user_naam}! Als beheerder heb je toegang tot alle functies.\n\nWat kan ik voor je doen?",
            2: f"💙 Hey {user_naam}! Fijn dat je er bent.\n\nIk ben Spark, en ik leer van elk gesprek. Vertel, waar kan ik je mee helpen?",
            3: f"🤝 Hallo {user_naam}! Leuk je te ontmoeten.\n\nIk ben Spark. Hoe gaat het met je?",
            4: f"👋 Hey {user_naam}!\n\nIk ben Spark, een lerende AI. Waarmee kan ik je helpen?",
            5: f"🌟 Hallo {user_naam}!\n\nWelkom bij Spark. Waar kan ik je mee helpen?",
            6: f"👋 Hoi {user_naam}!\n\nIk ben Spark. Hoe kan ik je helpen vandaag?",
            7: f"👋 Hallo {user_naam}!\n\nWelkom! Ik ben Spark, een AI-assistent. Waarmee kan ik je helpen?"
        }
        
        welcome = fallback_welcomes.get(gradatie, fallback_welcomes[7])
        print(f"[FIRST_MSG] Using fallback for gradatie {gradatie}")
        
        return welcome

        response = "Ik ben Spark, een lerende AI gemaakt door Willem Spakman (Roadkill).\n\n"
        response += "💡 Wat ik doe:\n"
        for wat in self.spark_identity.get("basis_kennis", {}).get("wat_ik_kan", [])[:3]:
            response += f"• {wat}\n"
        response += "\n"
        response += f"🎯 Mijn doel: {self.spark_identity.get('doel', '')}\n\n"
        response += "Ik begin leeg en leer van elk gesprek. Hoe meer we praten, hoe beter ik je kan helpen!"
        return response
    
    def _detect_mood_from_text(self, text: str) -> Optional[str]:
        """
        Detect mood from text content
        """
        text_lower = text.lower()
        
        # Positive indicators
        positive_words = ["goed", "fijn", "geweldig", "super", "yes", "top", "mooi", "leuk", "blij", "happy", "gelukkig"]
        # Sad indicators
        sad_words = ["verdrietig", "shit", "slecht", "bagger", "rot", "kut", "down", "depri", "moe"]
        # Angry indicators
        angry_words = ["boos", "irritant", "fucked", "kwaad", "pissed", "geïrriteerd"]
        # Enthusiastic indicators
        enthusiast_words = ["enthousiast", "excited", "energie", "gemotiveerd", "wauw", "wow"]
        
        # Count matches
        if any(word in text_lower for word in enthusiast_words):
            return "enthousiast"
        elif any(word in text_lower for word in angry_words):
            return "boos"
        elif any(word in text_lower for word in sad_words):
            return "verdrietig"
        elif any(word in text_lower for word in positive_words):
            return "blij"
        
        return "neutraal"
    
    def _get_help_text(self, user_data: Optional[Dict]) -> str:
        """
        Get help text based on user's gradatie
        """
        if not user_data:
            response = "📖 **Help - Niet ingelogd**\n\n"
            response += "Om mij te gebruiken, moet je eerst inloggen:\n\n"
            response += "🔑 **Aanmelden:**\n"
            response += "• 'Ik ben [naam] en mijn sleutelwoord is [woord]'\n"
            response += "• '[Naam] [Sleutelwoord]' (bijv: 'Willem Appelsap')\n"
            response += "• Voor admin: 'Ik ben [naam] mijn Masterkey is [woord]'\n\n"
            response += "Type 'wie ben je?' om meer over mij te weten!"
            return response
        
        gradatie = user_data.get('gradatie', 7)
        naam = user_data.get('naam', 'vriend')
        
        response = f"📖 **Help voor {naam}** (Gradatie {gradatie})\n\n"
        
        # Basic commands for everyone
        response += "🔹 **Basis commando's:**\n"
        response += "• 'Wie ben je?' - Over Spark\n"
        response += "• 'Wie ben ik?' - Jouw profiel\n"
        response += "• 'Onthoud [info]' - Leer mij iets nieuws\n"
        response += "• 'Wat weet je over [onderwerp]?' - Zoek kennis\n"
        response += "• 'Afmelden' - Uitloggen\n\n"
        
        # Gradatie-specific features
        if gradatie <= 5:
            response += "📖 **Dagboek:**\n"
            response += "• 'Dagboek entry: [tekst]' - Schrijf dagboek\n"
            response += "• 'Laat mijn dagboek zien' - Bekijk entries\n\n"
        
        if gradatie <= 3:
            response += "📊 **Gevorderde functies:**\n"
            response += "• Sentiment analyse van gesprekken\n"
            response += "• Automatische topic classificatie\n"
            response += "• Persoonlijke analytics\n\n"
        
        if gradatie == 1:
            response += "👑 **Admin functies:**\n"
            response += "• `/triggers` - Beheer emotie trigger lijsten (self-service!)\n"
            response += "• `emotie: [naam] [minuten]` - Stel emotie in (bijv. 'emotie: blij 30')\n"
            response += "• `emotie: reset` - Reset naar neutral\n"
            response += "• `note: [tekst]` - Snel notitie toevoegen\n"
            response += "• Systeem status monitoring\n"
            response += "• Gebruikersbeheer\n"
            response += "• Knowledge base beheer\n\n"
            response += "💡 Emoties: blij, vrolijk, euforie, boos, woede, verdrietig, somber, bang, voorzichtig, paniek\n\n"
        
        response += "💡 **Tips:**\n"
        response += "• Ik leer van elk gesprek met je\n"
        response += "• Je kunt me vragen stellen in natuurlijke taal\n"
        response += "• Ik ben tolerant voor typefouten\n\n"
        
        response += "Type 'wat kan ik nu?' om deze help opnieuw te zien!"
        
        return response
