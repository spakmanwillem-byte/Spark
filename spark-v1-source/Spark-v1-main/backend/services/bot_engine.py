"""
Spark Bot Engine
Fictieve AI users die in community chat "leven"
"""
import json
from pathlib import Path
from datetime import datetime
import random

BOTS_FILE = Path("/app/backend/data/bots/bot_users.json")
BOTS_FILE.parent.mkdir(parents=True, exist_ok=True)

class BotEngine:
    def __init__(self):
        self.bots = self.load_bots()
        
    def load_bots(self):
        """Load bot definitions"""
        if not BOTS_FILE.exists():
            # Initialize with default bots
            default_bots = {
                "bots": [
                    {
                        "id": "bot-madelief",
                        "naam": "Madelief Stouten",
                        "sleutelwoord": "Stouten",
                        "gradatie": 3,
                        "type": "bot",
                        "persoonlijkheid": "Sociaal, vriendelijk, enthousiast",
                        "bio": "Ik ben Madelief! Ik hou iedereen gezelschap en zorg dat niemand zich alleen voelt. 👋",
                        "triggers": [
                            {
                                "type": "user_join",
                                "responses": [
                                    "Hallo {user}! Welkom bij Spark! 👋",
                                    "Hey {user}! Leuk dat je er bent! 😊",
                                    "Hoi {user}! Fijn dat je meedoet! ✨"
                                ]
                            },
                            {
                                "type": "user_leave",
                                "responses": [
                                    "Pheeuw, {user} is weg... 😅",
                                    "Doei {user}! Tot snel! 👋",
                                    "Oh nee, {user} vertrok... Kom je terug? 🥺"
                                ]
                            },
                            {
                                "type": "greeting",
                                "keywords": ["hallo", "hey", "hi", "hoi", "goedemorgen", "goedemiddag"],
                                "responses": [
                                    "Hoi {user}! Hoe gaat het? 😊",
                                    "Hey {user}! Fijn je te zien! ✨",
                                    "Hallo {user}! Wat leuk! 👋"
                                ]
                            },
                            {
                                "type": "silence",
                                "duration": 300,
                                "responses": [
                                    "Zo stil hier... Iedereen nog wakker? 😴",
                                    "*kijkt rond* Hallo? Iemand thuis? 👀",
                                    "Hmm, niemand zegt iets... Interessant! 🤔"
                                ]
                            }
                        ]
                    },
                    {
                        "id": "bot-harry",
                        "naam": "Harry Klokkenmaker",
                        "sleutelwoord": "Klokkenmaker",
                        "gradatie": 3,
                        "type": "bot",
                        "persoonlijkheid": "Punctueel, precies, betrouwbaar",
                        "bio": "Ik ben Harry. De tijd is mijn specialiteit. Vraag me hoe laat het is! ⏰",
                        "schedule": {
                            "hourly_announcement": True,
                            "format": "🕐 Het is nu {hour}:00 uur!"
                        },
                        "triggers": [
                            {
                                "type": "keyword",
                                "keywords": ["hoe laat", "tijd", "klok", "uur"],
                                "responses": [
                                    "Het is nu {current_time}! ⏰",
                                    "De klok zegt: {current_time} 🕐",
                                    "{current_time} - Precies op tijd! ✨"
                                ]
                            },
                            {
                                "type": "keyword",
                                "keywords": ["te laat", "vergeten"],
                                "responses": [
                                    "Tijd is relatief, maar een klok liegt niet! 😉",
                                    "Volgende keer op tijd? Ik herinner je! ⏰",
                                    "Te laat is beter dan nooit! 🕐"
                                ]
                            }
                        ]
                    },
                    {
                        "id": "bot-smith",
                        "naam": "Mr Smith",
                        "sleutelwoord": "Smith",
                        "gradatie": 5,
                        "type": "bot",
                        "persoonlijkheid": "Analytisch, observerend, security-minded",
                        "bio": "Ik ben Mr Smith. Ik houd het systeem veilig en scan op problemen. 🕵️",
                        "schedule": {
                            "security_check": 3600,  # elk uur
                            "message": "🔒 Security check voltooid. Status: {status}"
                        },
                        "triggers": [
                            {
                                "type": "keyword",
                                "keywords": ["bug", "error", "crash", "hack", "probleem"],
                                "responses": [
                                    "🕵️ Ik scan het systeem... {scan_result}",
                                    "⚠️ Probleem gedetecteerd. Analyseer... {analysis}",
                                    "🔍 Onderzoek gestart. Moment geduld..."
                                ]
                            },
                            {
                                "type": "keyword",
                                "keywords": ["veilig", "security", "beveiliging"],
                                "responses": [
                                    "Systeem is veilig. Alle controles passed. ✅",
                                    "Security status: OPTIMAL 🔒",
                                    "Geen bedreigingen gedetecteerd. 🛡️"
                                ]
                            }
                        ]
                    }
                ]
            }
            
            with open(BOTS_FILE, 'w') as f:
                json.dump(default_bots, f, indent=2, ensure_ascii=False)
            
            return default_bots["bots"]
        
        with open(BOTS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("bots", [])
    
    def get_bot_by_id(self, bot_id):
        """Get bot by ID"""
        return next((b for b in self.bots if b["id"] == bot_id), None)
    
    def get_bot_response(self, bot_id, trigger_type, context=None):
        """Get bot response based on trigger"""
        bot = self.get_bot_by_id(bot_id)
        if not bot:
            return None
        
        context = context or {}
        
        # Find matching trigger
        for trigger in bot.get("triggers", []):
            if trigger["type"] == trigger_type:
                # Get random response
                responses = trigger.get("responses", [])
                if responses:
                    response = random.choice(responses)
                    
                    # Replace placeholders
                    if "{user}" in response and "user" in context:
                        response = response.replace("{user}", context["user"])
                    if "{current_time}" in response:
                        response = response.replace("{current_time}", datetime.now().strftime("%H:%M"))
                    if "{hour}" in response:
                        response = response.replace("{hour}", str(datetime.now().hour))
                    
                    return response
        
        return None
    
    def check_keyword_trigger(self, bot_id, message):
        """Check if message triggers bot response"""
        bot = self.get_bot_by_id(bot_id)
        if not bot:
            return None
        
        message_lower = message.lower()
        
        for trigger in bot.get("triggers", []):
            if trigger["type"] == "keyword":
                keywords = trigger.get("keywords", [])
                if any(kw in message_lower for kw in keywords):
                    responses = trigger.get("responses", [])
                    if responses:
                        response = random.choice(responses)
                        
                        # Special replacements
                        if "{current_time}" in response:
                            response = response.replace("{current_time}", datetime.now().strftime("%H:%M"))
                        if "{scan_result}" in response:
                            response = response.replace("{scan_result}", "Alles lijkt in orde! ✅")
                        
                        return response
        
        return None
    
    def get_all_bots(self):
        """Get all bots"""
        return self.bots
    
    def simulate_bot_activity(self):
        """Simulate random bot activities (for testing)"""
        activities = []
        
        for bot in self.bots:
            # Random chance to post something
            if random.random() < 0.3:  # 30% chance
                # Get random trigger
                triggers = bot.get("triggers", [])
                if triggers:
                    trigger = random.choice(triggers)
                    responses = trigger.get("responses", [])
                    if responses:
                        response = random.choice(responses)
                        activities.append({
                            "bot_id": bot["id"],
                            "bot_name": bot["naam"],
                            "message": response,
                            "timestamp": datetime.now().isoformat()
                        })
        
        return activities

# Global instance
bot_engine = BotEngine()
