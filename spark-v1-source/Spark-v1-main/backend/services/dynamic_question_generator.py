"""
Dynamic Profile Question Generator
Generates personalized questions based on Spark's knowledge + user's conversation patterns
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from utils.data_manager import DataManager
from collections import Counter
import re


class DynamicQuestionGenerator:
    """
    Generates profile questions dynamically based on:
    - Spark's knowledge base (what Spark knows about)
    - User's conversation topics (what user talks about)
    - Spark's values (from spark_bijbel)
    - What's missing in user's profile
    """
    
    # Question templates per knowledge type
    QUESTION_TEMPLATES = {
        "technology": {
            "patterns": ["framework", "language", "tool", "platform", "technologie"],
            "questions": [
                "Ik zie dat je het vaak over {concept} hebt. Werk je daar dagelijks mee?",
                "Je praat regelmatig over {concept}. Gebruik je dat in je werk?",
                "Mag ik wat vragen? Heb je ervaring met {concept}?"
            ],
            "profile_field": "personal_info.werk.technologieën",
            "confirmation": "Oké, dus je werkt met {concept}?",
            "thanks": [
                "Nice! Dat is handig om te weten 💻",
                "Cool! Genoteerd in je tech stack.",
                "Mooi! Nu weet ik wat je gebruikt."
            ]
        },
        "location": {
            "patterns": ["stad", "plaats", "city", "locatie", "land"],
            "questions": [
                "Ik merk dat je {concept} vaak noemt. Woon je daar?",
                "Je hebt het regelmatig over {concept}. Ben je daar woonachtig?",
                "Mag ik wat vragen? Woon je in {concept}?"
            ],
            "profile_field": "personal_info.adres.plaats",
            "confirmation": "Dus je woont in {concept}?",
            "thanks": [
                "Ah nice! Genoteerd 🏠",
                "Mooi! Nu weet ik waar je zit.",
                "Top, dankjewel!"
            ]
        },
        "interest": {
            "patterns": ["hobby", "interesse", "passion", "sport", "muziek", "game"],
            "questions": [
                "Ik zie dat je geïnteresseerd bent in {concept}. Is dat een hobby van je?",
                "Je praat vaak over {concept}. Doe je dat in je vrije tijd?",
                "Mag ik wat vragen? Ben je fan van {concept}?"
            ],
            "profile_field": "personal_info.interesses.hobbies",
            "confirmation": "Dus {concept} is een hobby van je?",
            "thanks": [
                "Nice! Dat is gaaf om te weten 🎯",
                "Cool! Daar kunnen we het wel over hebben 😄",
                "Vet! Genoteerd."
            ]
        },
        "work": {
            "patterns": ["beroep", "werk", "job", "carrière", "functie", "rol"],
            "questions": [
                "Ik merk dat je {concept} vaak bespreekt. Is dat je beroep?",
                "Je hebt het regelmatig over {concept}. Werk je in die sector?",
                "Mag ik wat vragen? Ben je {concept}?"
            ],
            "profile_field": "personal_info.werk.beroep",
            "confirmation": "Oké, dus je bent {concept}?",
            "thanks": [
                "Nice! Dat is handig om te weten 💼",
                "Cool! Genoteerd.",
                "Mooi, dankjewel!"
            ]
        },
        "person": {
            "patterns": ["persoon", "relatie", "partner", "vriend", "familie"],
            "questions": [
                "Ik hoor je vaak over {concept} praten. Is dat belangrijk voor je?",
                "Je noemt {concept} regelmatig. Mag ik vragen wie dat is?",
                "Mag ik wat persoonlijks vragen? Je hebt het vaak over {concept}..."
            ],
            "profile_field": "personal_info.relaties",
            "confirmation": "Oké, dus {concept} is belangrijk voor je?",
            "thanks": [
                "Dankje voor het delen! 😊",
                "Mooi om te weten.",
                "Genoteerd!"
            ]
        }
    }
    
    @staticmethod
    def should_generate_question(user_data: Dict, conversation_count: int) -> bool:
        """
        Check if we should generate a dynamic question
        
        Criteria:
        - Conversation count % 5 == 0 (every 5 conversations)
        - User has at least 5 conversations (enough data)
        - Last question was >24h ago
        """
        # Minimum conversation count
        if conversation_count < 5:
            return False
        
        # Only every 5 conversations
        if conversation_count % 5 != 0:
            return False
        
        # Check last question time
        last_asked = user_data.get("dynamic_profile", {}).get("last_question_at")
        if last_asked:
            from datetime import datetime, timedelta
            last_time = datetime.fromisoformat(last_asked)
            if datetime.now() - last_time < timedelta(hours=24):
                return False
        
        return True
    
    @staticmethod
    def analyze_user_topics(user_id: str, limit: int = 20) -> Dict[str, int]:
        """
        Analyze user's recent conversations and extract frequent topics
        
        Returns:
            Dict of {topic: frequency}
        """
        try:
            conv_data = DataManager.load_data(f"conversations/user-{user_id}_conversations.json")
            conversations = conv_data.get("conversations", [])
        except:
            return {}
        
        # Get recent conversations
        recent = conversations[-limit:] if len(conversations) > limit else conversations
        
        # Extract topics from user messages
        all_words = []
        for conv in recent:
            message = conv.get("user_message", "").lower()
            # Remove common words
            words = re.findall(r'\b\w{4,}\b', message)  # Words 4+ chars
            all_words.extend(words)
        
        # Count frequency
        common_words = [
            "deze", "heeft", "zijn", "maar", "naar", "voor", "over", "omdat",
            "waar", "toen", "zoals", "tussen", "tijdens", "echter", "eigenlijk",
            "natuurlijk", "misschien", "gewoon", "echt", "heel", "veel", "meer"
        ]
        
        filtered = [w for w in all_words if w not in common_words and len(w) > 3]
        frequency = Counter(filtered)
        
        return dict(frequency.most_common(20))
    
    @staticmethod
    def match_topics_to_knowledge(user_topics: Dict[str, int]) -> List[Tuple[str, str, int]]:
        """
        Match user topics with Spark's knowledge base
        
        Returns:
            List of (concept, knowledge_type, relevance_score)
        """
        try:
            kb = DataManager.load_json("learned_knowledge/knowledge_base.json")
            entries = kb.get("knowledge_entries", [])
        except:
            return []
        
        matches = []
        
        for entry in entries:
            if entry.get("status") != "active":
                continue
            
            begrip = entry.get("begrip", "").lower()
            uitleg = entry.get("uitleg", "").lower()
            tags = entry.get("tags", [])
            
            # Check if this knowledge entry is relevant to user's topics
            relevance = 0
            matched_topic = None
            
            for topic, freq in user_topics.items():
                topic_lower = topic.lower()
                
                # Direct match in begrip
                if topic_lower in begrip or begrip in topic_lower:
                    relevance = freq * 10
                    matched_topic = begrip
                    break
                
                # Match in uitleg
                if topic_lower in uitleg:
                    relevance = freq * 5
                    matched_topic = begrip
                    break
                
                # Match in tags
                if any(topic_lower in tag.lower() for tag in tags):
                    relevance = freq * 3
                    matched_topic = begrip
                    break
            
            if relevance > 0 and matched_topic:
                # Determine knowledge type from tags
                knowledge_type = DynamicQuestionGenerator._determine_type_from_tags(tags)
                matches.append((matched_topic, knowledge_type, relevance))
        
        # Sort by relevance
        matches.sort(key=lambda x: x[2], reverse=True)
        
        return matches[:5]  # Top 5
    
    @staticmethod
    def _determine_type_from_tags(tags: List[str]) -> str:
        """Determine question type from knowledge entry tags"""
        tags_lower = [t.lower() for t in tags]
        
        if any(t in tags_lower for t in ["technologie", "framework", "tool", "programming", "code"]):
            return "technology"
        elif any(t in tags_lower for t in ["plaats", "stad", "land", "locatie"]):
            return "location"
        elif any(t in tags_lower for t in ["hobby", "sport", "muziek", "game", "interesse"]):
            return "interest"
        elif any(t in tags_lower for t in ["werk", "beroep", "carrière", "functie"]):
            return "work"
        elif any(t in tags_lower for t in ["persoon", "relatie", "familie"]):
            return "person"
        else:
            return "interest"  # Default
    
    @staticmethod
    def check_if_already_in_profile(user_data: Dict, concept: str, knowledge_type: str) -> bool:
        """Check if this concept is already in user's profile"""
        profile = user_data.get("personal_info", {})
        
        if knowledge_type == "technology":
            tech_list = profile.get("werk", {}).get("technologieën", [])
            return any(concept.lower() in str(tech).lower() for tech in tech_list)
        
        elif knowledge_type == "location":
            plaats = profile.get("adres", {}).get("plaats", "")
            return concept.lower() in plaats.lower() if plaats else False
        
        elif knowledge_type == "work":
            beroep = profile.get("werk", {}).get("beroep", "")
            return concept.lower() in beroep.lower() if beroep else False
        
        elif knowledge_type == "interest":
            hobbies = profile.get("interesses", {}).get("hobbies", [])
            if isinstance(hobbies, list):
                return any(concept.lower() in str(h).lower() for h in hobbies)
            elif isinstance(hobbies, str):
                return concept.lower() in hobbies.lower()
        
        return False
    
    @staticmethod
    def generate_question(user_data: Dict) -> Optional[Dict]:
        """
        Generate a dynamic profile question based on user's behavior and Spark's knowledge
        
        Returns:
            {
                "concept": str,
                "type": str,
                "question": str,
                "confirmation": str,
                "thanks": str,
                "profile_field": str
            }
        """
        user_id = user_data.get("id")
        
        # Get conversation count
        try:
            conv_data = DataManager.load_data(f"conversations/user-{user_id}_conversations.json")
            conversation_count = len(conv_data.get("conversations", []))
        except:
            conversation_count = 0
        
        # Check if we should ask
        if not DynamicQuestionGenerator.should_generate_question(user_data, conversation_count):
            return None
        
        # Analyze user's topics
        user_topics = DynamicQuestionGenerator.analyze_user_topics(user_id)
        
        if not user_topics:
            return None
        
        # Match with knowledge
        matches = DynamicQuestionGenerator.match_topics_to_knowledge(user_topics)
        
        if not matches:
            return None
        
        # Find first concept not already in profile
        for concept, knowledge_type, relevance in matches:
            if DynamicQuestionGenerator.check_if_already_in_profile(user_data, concept, knowledge_type):
                continue  # Skip, already known
            
            # Generate question
            template = DynamicQuestionGenerator.QUESTION_TEMPLATES.get(knowledge_type)
            if not template:
                continue
            
            import random
            question_text = random.choice(template["questions"]).format(concept=concept)
            confirmation = template["confirmation"].format(concept=concept)
            thanks = random.choice(template["thanks"])
            
            # Save state
            users = DataManager.load_users()
            user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
            
            if user_index is not None:
                if "dynamic_profile" not in users[user_index]:
                    users[user_index]["dynamic_profile"] = {}
                
                users[user_index]["dynamic_profile"]["last_question_at"] = datetime.now().isoformat()
                users[user_index]["dynamic_profile"]["current_concept"] = concept
                users[user_index]["dynamic_profile"]["current_type"] = knowledge_type
                users[user_index]["dynamic_profile"]["state"] = "waiting_answer"
                
                DataManager.save_users(users)
            
            return {
                "concept": concept,
                "type": knowledge_type,
                "question": question_text,
                "confirmation": confirmation,
                "thanks": thanks,
                "profile_field": template["profile_field"]
            }
        
        return None
    
    @staticmethod
    def handle_answer(user_data: Dict, message: str) -> Optional[str]:
        """Handle user's answer to dynamic question"""
        message_lower = message.lower().strip()
        
        # Detect yes/no
        is_yes = any(word in message_lower for word in ["ja", "yes", "klopt", "inderdaad", "zeker", "precies", "dagelijks", "vaak"])
        is_no = any(word in message_lower for word in ["nee", "no", "niet", "nooit"])
        
        if is_no:
            # User says no - clear state and don't ask again
            DynamicQuestionGenerator.cancel_question(user_data)
            return "Ah oké, thanks voor het laten weten! 👍"
        
        if is_yes:
            # Confirm
            concept = user_data.get("dynamic_profile", {}).get("current_concept")
            question_data = DynamicQuestionGenerator.QUESTION_TEMPLATES.get(
                user_data.get("dynamic_profile", {}).get("current_type")
            )
            
            if question_data and concept:
                # Update state to confirming
                user_id = user_data.get("id")
                users = DataManager.load_users()
                user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
                
                if user_index is not None:
                    users[user_index]["dynamic_profile"]["state"] = "confirming"
                    DataManager.save_users(users)
                
                return question_data["confirmation"].format(concept=concept)
        
        return None
    
    @staticmethod
    def handle_confirmation(user_data: Dict, message: str) -> Optional[str]:
        """Handle confirmation and save to profile"""
        message_lower = message.lower().strip()
        
        is_yes = any(word in message_lower for word in ["ja", "yes", "klopt", "correct", "juist"])
        is_no = any(word in message_lower for word in ["nee", "no", "niet"])
        
        concept = user_data.get("dynamic_profile", {}).get("current_concept")
        knowledge_type = user_data.get("dynamic_profile", {}).get("current_type")
        
        if is_no:
            DynamicQuestionGenerator.cancel_question(user_data)
            return "Oeps, dan heb ik het verkeerd begrepen 😅"
        
        if is_yes and concept and knowledge_type:
            # Save to profile
            success = DynamicQuestionGenerator.save_to_profile(user_data, concept, knowledge_type)
            
            if success:
                DynamicQuestionGenerator.complete_question(user_data)
                template = DynamicQuestionGenerator.QUESTION_TEMPLATES.get(knowledge_type)
                import random
                return random.choice(template["thanks"]) if template else "Dankjewel! Genoteerd."
            else:
                DynamicQuestionGenerator.cancel_question(user_data)
                return "Hmm, er ging iets mis met opslaan 😕"
        
        return None
    
    @staticmethod
    def save_to_profile(user_data: Dict, concept: str, knowledge_type: str) -> bool:
        """Save concept to appropriate profile field"""
        try:
            user_id = user_data.get("id")
            from services.profile_service import ProfileService
            
            if knowledge_type == "technology":
                # Add to tech list
                current_tech = user_data.get("personal_info", {}).get("werk", {}).get("technologieën", [])
                if not isinstance(current_tech, list):
                    current_tech = []
                if concept not in current_tech:
                    current_tech.append(concept)
                return ProfileService.update_profile_field(user_id, "personal_info.werk.technologieën", current_tech)
            
            elif knowledge_type == "location":
                return ProfileService.update_profile_field(user_id, "personal_info.adres.plaats", concept)
            
            elif knowledge_type == "work":
                return ProfileService.update_profile_field(user_id, "personal_info.werk.beroep", concept)
            
            elif knowledge_type == "interest":
                current_hobbies = user_data.get("personal_info", {}).get("interesses", {}).get("hobbies", [])
                if not isinstance(current_hobbies, list):
                    current_hobbies = [current_hobbies] if current_hobbies else []
                if concept not in current_hobbies:
                    current_hobbies.append(concept)
                return ProfileService.update_profile_field(user_id, "personal_info.interesses.hobbies", current_hobbies)
            
            return False
        except Exception as e:
            print(f"Error saving to profile: {e}")
            return False
    
    @staticmethod
    def cancel_question(user_data: Dict):
        """Cancel current question"""
        user_id = user_data.get("id")
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is not None:
            users[user_index]["dynamic_profile"] = {}
            DataManager.save_users(users)
    
    @staticmethod
    def complete_question(user_data: Dict):
        """Mark question as completed"""
        user_id = user_data.get("id")
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is not None:
            users[user_index]["dynamic_profile"]["state"] = "completed"
            users[user_index]["dynamic_profile"]["completed_at"] = datetime.now().isoformat()
            DataManager.save_users(users)
    
    @staticmethod
    def get_current_state(user_data: Dict) -> Optional[str]:
        """Get current question state"""
        return user_data.get("dynamic_profile", {}).get("state")
