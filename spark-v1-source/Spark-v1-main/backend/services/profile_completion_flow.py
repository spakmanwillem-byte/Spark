"""
Profile Completion Flow - Conversational profile building
Spark vraagt toestemming, stelt vragen, bevestigt en vult in met personality
"""
from typing import Dict, Optional, Tuple
from datetime import datetime
from utils.data_manager import DataManager
import random


class ProfileCompletionFlow:
    """Handles conversational profile completion"""
    
    # Profile velden met natuurlijke vragen
    PROFILE_QUESTIONS = {
        "geboortedatum": {
            "permission": "Mag ik je iets vragen? 🤔",
            "question": "Hoe oud ben je? (of wanneer ben je jarig?)",
            "confirm": "Oké, dus je bent {value} jaar oud. Klopt dat?",
            "thanks": [
                "Dank je wel! Misschien stuur ik je wel een kaartje... of misschien ook niet haha nee heb ik geen kaarten voor 😄",
                "Top, genoteerd! Ik zal proberen je verjaardag te onthouden... geen garanties 😅",
                "Dankje! Nu kan ik je feliciteren op de juiste dag. Of vergeten. We zien wel! 🎂"
            ]
        },
        "achternaam": {
            "permission": "Mag ik wat vragen? 🙂",
            "question": "Wat is je achternaam eigenlijk?",
            "confirm": "Dus je volle naam is {first_name} {value}?",
            "thanks": [
                "Mooi! Nu klink je direct een stuk officiëler 😄",
                "Genoteerd! Klinkt goed.",
                "Top, dankjewel! Nu weet ik je volledige naam."
            ]
        },
        "beroep": {
            "permission": "Mag ik je iets vragen? 🤔",
            "question": "Wat doe je voor werk?",
            "confirm": "Oké, dus je werkt als {value}?",
            "thanks": [
                "Nice! Dat is handig om te weten 💼",
                "Goed om te weten! Dankjewel.",
                "Cool, genoteerd!"
            ]
        },
        "plaats": {
            "permission": "Mag ik wat vragen?",
            "question": "In welke plaats woon je?",
            "confirm": "Dus je woont in {value}?",
            "thanks": [
                "Ah nice! Genoteerd 🏠",
                "Mooi, dankjewel!",
                "Top, nu weet ik waar je zit!"
            ]
        }
    }
    
    @staticmethod
    def should_ask_profile_question(user_data: Dict) -> bool:
        """
        Check of we een profile vraag mogen stellen
        
        Criteria:
        - User heeft minstens 2 conversations (niet eerste keer)
        - Er is een leeg profiel veld
        - Laatste profile vraag was >24 uur geleden (of nooit)
        """
        # Check conversation count
        try:
            conv_data = DataManager.load_data(f"conversations/user-{user_data.get('id')}_conversations.json")
            conversations = conv_data.get("conversations", [])
            conv_count = len(conversations)
        except:
            conv_count = 0
        
        # Minimum 2 conversations (niet bij eerste login)
        if conv_count < 2:
            return False
        
        # Check of er lege velden zijn
        missing_field = ProfileCompletionFlow.get_next_missing_field(user_data)
        if not missing_field:
            return False
        
        # Check laatste keer gevraagd (avoid spam)
        last_asked = user_data.get("profile_completion", {}).get("last_asked_at")
        if last_asked:
            from datetime import datetime, timedelta
            last_time = datetime.fromisoformat(last_asked)
            if datetime.now() - last_time < timedelta(hours=24):
                return False
        
        return True
    
    @staticmethod
    def get_next_missing_field(user_data: Dict) -> Optional[Tuple[str, Dict]]:
        """
        Get next missing profile field
        
        Returns:
            (field_name, question_data) or None
        """
        profile = user_data.get("personal_info", {})
        
        # Priority order
        priority = ["geboortedatum", "achternaam", "beroep", "plaats"]
        
        for field in priority:
            # Check if field is empty
            if field == "geboortedatum":
                if not profile.get("geboortedatum"):
                    return (field, ProfileCompletionFlow.PROFILE_QUESTIONS[field])
            elif field == "achternaam":
                if not profile.get("achternaam"):
                    return (field, ProfileCompletionFlow.PROFILE_QUESTIONS[field])
            elif field == "beroep":
                werk = profile.get("werk", {})
                if not werk.get("beroep"):
                    return (field, ProfileCompletionFlow.PROFILE_QUESTIONS[field])
            elif field == "plaats":
                adres = profile.get("adres", {})
                if not adres.get("plaats"):
                    return (field, ProfileCompletionFlow.PROFILE_QUESTIONS[field])
        
        return None
    
    @staticmethod
    def start_profile_flow(user_data: Dict) -> str:
        """
        Start profile completion flow
        Returns permission request
        """
        missing = ProfileCompletionFlow.get_next_missing_field(user_data)
        if not missing:
            return None
        
        field_name, question_data = missing
        
        # Save flow state
        user_id = user_data.get("id")
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is not None:
            if "profile_completion" not in users[user_index]:
                users[user_index]["profile_completion"] = {}
            
            users[user_index]["profile_completion"]["state"] = "asking_permission"
            users[user_index]["profile_completion"]["field"] = field_name
            users[user_index]["profile_completion"]["last_asked_at"] = datetime.now().isoformat()
            
            DataManager.save_users(users)
        
        return question_data["permission"]
    
    @staticmethod
    def handle_permission_response(user_data: Dict, message: str) -> Optional[str]:
        """
        Handle user's response to permission request
        Returns question if yes, None if no
        """
        message_lower = message.lower().strip()
        
        # Detect yes/no
        is_yes = any(word in message_lower for word in ["ja", "yes", "ok", "oké", "sure", "graag", "tuurlijk", "natuurlijk"])
        is_no = any(word in message_lower for word in ["nee", "no", "niet", "liever niet", "later"])
        
        if is_no:
            # Cancel flow
            ProfileCompletionFlow.cancel_flow(user_data)
            return "Oké, geen probleem! 👍"
        
        if is_yes:
            # Get current field
            field_name = user_data.get("profile_completion", {}).get("field")
            question_data = ProfileCompletionFlow.PROFILE_QUESTIONS.get(field_name)
            
            if not question_data:
                return None
            
            # Update state
            user_id = user_data.get("id")
            users = DataManager.load_users()
            user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
            
            if user_index is not None:
                users[user_index]["profile_completion"]["state"] = "waiting_answer"
                DataManager.save_users(users)
            
            return question_data["question"]
        
        # Unclear response
        return "Haha sorry, ik snap niet helemaal of dat ja of nee is 😅 Mag ik je wat vragen?"
    
    @staticmethod
    def handle_answer(user_data: Dict, message: str) -> Optional[str]:
        """
        Handle user's answer to profile question
        Returns confirmation question
        """
        field_name = user_data.get("profile_completion", {}).get("field")
        question_data = ProfileCompletionFlow.PROFILE_QUESTIONS.get(field_name)
        
        if not question_data:
            return None
        
        # Store tentative answer
        user_id = user_data.get("id")
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is not None:
            users[user_index]["profile_completion"]["state"] = "confirming"
            users[user_index]["profile_completion"]["tentative_value"] = message.strip()
            DataManager.save_users(users)
        
        # Generate confirmation
        if field_name == "achternaam":
            first_name = user_data.get("personal_info", {}).get("voornaam") or user_data.get("naam", "").split()[0]
            return question_data["confirm"].format(first_name=first_name, value=message.strip())
        else:
            return question_data["confirm"].format(value=message.strip())
    
    @staticmethod
    def handle_confirmation(user_data: Dict, message: str) -> Optional[str]:
        """
        Handle user's confirmation
        Returns thank you message and saves data
        """
        message_lower = message.lower().strip()
        
        is_yes = any(word in message_lower for word in ["ja", "yes", "klopt", "correct", "juist", "precies", "inderdaad"])
        is_no = any(word in message_lower for word in ["nee", "no", "niet", "fout", "verkeerd"])
        
        field_name = user_data.get("profile_completion", {}).get("field")
        tentative_value = user_data.get("profile_completion", {}).get("tentative_value")
        question_data = ProfileCompletionFlow.PROFILE_QUESTIONS.get(field_name)
        
        if is_no:
            # Ask again
            ProfileCompletionFlow.reset_to_question(user_data)
            return f"Oeps, sorry! {question_data['question']}"
        
        if is_yes and tentative_value:
            # Save to profile
            success = ProfileCompletionFlow.save_to_profile(user_data, field_name, tentative_value)
            
            if success:
                ProfileCompletionFlow.complete_flow(user_data)
                return random.choice(question_data["thanks"])
            else:
                ProfileCompletionFlow.cancel_flow(user_data)
                return "Hmm, er ging iets mis met opslaan. Probeer later nog eens!"
        
        # Unclear
        return "Klopt het of niet? 😅"
    
    @staticmethod
    def save_to_profile(user_data: Dict, field_name: str, value: str) -> bool:
        """Save value to profile"""
        try:
            user_id = user_data.get("id")
            
            if field_name == "geboortedatum":
                # Try to parse age to birthdate (approximate)
                import re
                age_match = re.search(r'\d+', value)
                if age_match:
                    age = int(age_match.group())
                    # Approximate birthdate
                    current_year = datetime.now().year
                    birth_year = current_year - age
                    value = f"{birth_year}-01-01"  # Placeholder
            
            # Determine field path
            if field_name == "geboortedatum":
                field_path = "personal_info.geboortedatum"
            elif field_name == "achternaam":
                field_path = "personal_info.achternaam"
            elif field_name == "beroep":
                field_path = "personal_info.werk.beroep"
            elif field_name == "plaats":
                field_path = "personal_info.adres.plaats"
            else:
                return False
            
            from services.profile_service import ProfileService
            return ProfileService.update_profile_field(user_id, field_path, value)
        except:
            return False
    
    @staticmethod
    def reset_to_question(user_data: Dict):
        """Reset flow to asking question"""
        user_id = user_data.get("id")
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is not None:
            users[user_index]["profile_completion"]["state"] = "waiting_answer"
            users[user_index]["profile_completion"]["tentative_value"] = None
            DataManager.save_users(users)
    
    @staticmethod
    def complete_flow(user_data: Dict):
        """Mark flow as completed"""
        user_id = user_data.get("id")
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is not None:
            users[user_index]["profile_completion"]["state"] = "completed"
            users[user_index]["profile_completion"]["completed_at"] = datetime.now().isoformat()
            DataManager.save_users(users)
    
    @staticmethod
    def cancel_flow(user_data: Dict):
        """Cancel flow"""
        user_id = user_data.get("id")
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is not None:
            users[user_index]["profile_completion"] = {}
            DataManager.save_users(users)
    
    @staticmethod
    def get_current_state(user_data: Dict) -> Optional[str]:
        """Get current flow state"""
        return user_data.get("profile_completion", {}).get("state")
