"""
Spark Conversation Trainer - Automated Learning via Simulated Conversations
Train Spark by simulating realistic conversations with bot users (Madelief, Harry, Mr Smith)
"""
import sys
import os
sys.path.append('/app/backend')

import requests
import json
import time
import random
from typing import List, Dict
from datetime import datetime


class ConversationTrainer:
    """
    Simuleert gesprekken met Spark om knowledge base uit te breiden
    """
    
    def __init__(self, api_url: str = "https://spark-foundation.preview.emergentagent.com"):
        self.api_url = api_url
        
        # Bot users met hun karakteristieken
        self.bots = {
            "madelief": {
                "user_id": "bot-madelief",
                "naam": "Madelief Stouten",
                "sleutelwoord": "Stouten",
                "personality": "Sociaal, vriendelijk, enthousiast",
                "topics": ["community", "mensen", "verbinding", "feesten", "events"],
                "conversation_style": "open, vrolijk, veel emoji's"
            },
            "harry": {
                "user_id": "bot-harry",
                "naam": "Harry Klokkenmaker",
                "sleutelwoord": "Klokkenmaker",
                "personality": "Punctueel, precies, betrouwbaar",
                "topics": ["tijd", "planning", "afspraken", "deadlines", "routine"],
                "conversation_style": "kort, to the point, tijdsbewust"
            },
            "smith": {
                "user_id": "bot-smith",
                "naam": "Mr Smith",
                "sleutelwoord": "Smith",
                "personality": "Professioneel, veiligheid, quality control",
                "topics": ["security", "bugs", "errors", "testing", "kwaliteit"],
                "conversation_style": "formeel, analytisch, kritisch"
            }
        }
        
        # Conversation scenarios per bot
        self.scenarios = self._load_scenarios()
    
    def _load_scenarios(self) -> Dict:
        """
        Laad gespreksscenario's per bot
        """
        return {
            "madelief": [
                {
                    "title": "Community Event Planning",
                    "messages": [
                        "Hoi Spark! 👋",
                        "Ik wil graag een community event organiseren volgende maand",
                        "Wat denk je van een gezellige borrel?",
                        "Ja leuk! Kunnen we dan ook wat spelletjes doen?",
                        "Super! Dankjewel voor de suggesties"
                    ]
                },
                {
                    "title": "Nieuwe Mensen Verwelkomen",
                    "messages": [
                        "Hey Spark!",
                        "Er zijn 3 nieuwe mensen in de community!",
                        "Hoe kan ik ze het beste verwelkomen?",
                        "Goed idee! Ik ga dat doen",
                        "Dankje! 😊"
                    ]
                },
                {
                    "title": "Dagelijkse Check-in",
                    "messages": [
                        "Goedemorgen Spark! ☀️",
                        "Hoe is het met je?",
                        "Mooi! Vandaag wordt een fijne dag",
                        "Tot later! 👋"
                    ]
                }
            ],
            "harry": [
                {
                    "title": "Tijd Management",
                    "messages": [
                        "Spark, hoe laat is het?",
                        "Ik moet om 14:00 een afspraak",
                        "Kun je me herinneren?",
                        "Bedankt"
                    ]
                },
                {
                    "title": "Planning Check",
                    "messages": [
                        "Wat staat er deze week op mijn agenda?",
                        "Hoeveel afspraken heb ik morgen?",
                        "Oké, genoteerd",
                        "Tot morgen"
                    ]
                },
                {
                    "title": "Routine Tracking",
                    "messages": [
                        "Goedemorgen",
                        "Ik begin aan mijn dagelijkse routine",
                        "Eerst koffie, dan werk",
                        "Klaar voor vandaag"
                    ]
                }
            ],
            "smith": [
                {
                    "title": "Security Check",
                    "messages": [
                        "Spark, status rapport",
                        "Zijn er bugs of errors gedetecteerd?",
                        "Systeem integriteit check",
                        "Acknowledged",
                        "Continue monitoring"
                    ]
                },
                {
                    "title": "Quality Assurance",
                    "messages": [
                        "Ik test de nieuwe features",
                        "Uitgaven module werkt correct",
                        "Inkomsten module ook in orde",
                        "Dagboek module functioneert",
                        "All systems operational"
                    ]
                },
                {
                    "title": "Performance Analysis",
                    "messages": [
                        "Response tijd analyse",
                        "Wat is de gemiddelde response tijd?",
                        "Acceptabel",
                        "Rapport afgesloten"
                    ]
                }
            ]
        }
    
    def chat(self, user_id: str, message: str) -> Dict:
        """
        Stuur een chat bericht naar Spark
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/chat",
                json={
                    "message": message,
                    "user_id": user_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Status {response.status_code}"}
        
        except Exception as e:
            return {"error": str(e)}
    
    def run_scenario(self, bot_name: str, scenario: Dict, delay: float = 2.0) -> List[Dict]:
        """
        Voer een scenario uit met een bot
        
        Args:
            bot_name: "madelief", "harry", of "smith"
            scenario: Scenario dict met messages
            delay: Seconden tussen berichten
        
        Returns:
            Lijst van conversation exchanges
        """
        bot = self.bots[bot_name]
        user_id = bot["user_id"]
        
        print(f"\n{'='*60}")
        print(f"🎭 SCENARIO: {scenario['title']}")
        print(f"👤 BOT: {bot['naam']}")
        print(f"{'='*60}\n")
        
        # First: Login
        login_message = f"Ik ben {bot['naam']} sleutelwoord {bot['sleutelwoord']}"
        print(f"[LOGIN] {bot['naam']}: {login_message}")
        login_response = self.chat(user_id, login_message)
        
        if "error" not in login_response:
            print(f"   ✅ Logged in!")
        else:
            print(f"   ⚠️ Login issue: {login_response.get('error')}")
        
        time.sleep(1)
        
        exchanges = []
        
        for idx, message in enumerate(scenario["messages"], 1):
            print(f"[{idx}/{len(scenario['messages'])}] {bot['naam']}: {message}")
            
            # Send message
            response_data = self.chat(user_id, message)
            
            if "error" in response_data:
                print(f"   ❌ Error: {response_data['error']}")
                exchanges.append({
                    "user_message": message,
                    "spark_response": None,
                    "error": response_data["error"]
                })
            else:
                spark_response = response_data.get("response", "No response")
                print(f"   🤖 Spark: {spark_response[:150]}...")
                
                exchanges.append({
                    "user_message": message,
                    "spark_response": spark_response,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Wait before next message (natuurlijk gesprek)
            if idx < len(scenario["messages"]):
                time.sleep(delay)
        
        print(f"\n✅ Scenario '{scenario['title']}' completed!\n")
        
        return exchanges
    
    def run_training_session(
        self,
        bots: List[str] = None,
        scenarios_per_bot: int = 2,
        delay: float = 2.0
    ) -> Dict:
        """
        Run een complete training sessie met meerdere bots
        
        Args:
            bots: Lijst van bot namen (None = alle bots)
            scenarios_per_bot: Hoeveel scenarios per bot
            delay: Seconden tussen berichten
        
        Returns:
            Training rapport
        """
        if bots is None:
            bots = ["madelief", "harry", "smith"]
        
        print(f"\n🚀 SPARK TRAINING SESSION STARTED")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🤖 Bots: {', '.join(bots)}")
        print(f"📊 Scenarios per bot: {scenarios_per_bot}")
        
        all_exchanges = {}
        
        for bot_name in bots:
            bot_scenarios = self.scenarios[bot_name]
            
            # Selecteer scenarios (random of eerste X)
            selected = random.sample(bot_scenarios, min(scenarios_per_bot, len(bot_scenarios)))
            
            bot_exchanges = []
            
            for scenario in selected:
                exchanges = self.run_scenario(bot_name, scenario, delay)
                bot_exchanges.extend(exchanges)
            
            all_exchanges[bot_name] = bot_exchanges
        
        # Create rapport
        rapport = {
            "timestamp": datetime.now().isoformat(),
            "bots_trained": bots,
            "total_messages": sum(len(exchanges) for exchanges in all_exchanges.values()),
            "exchanges": all_exchanges
        }
        
        print(f"\n{'='*60}")
        print(f"✅ TRAINING SESSION COMPLETED")
        print(f"📊 Total messages: {rapport['total_messages']}")
        print(f"{'='*60}\n")
        
        return rapport
    
    def save_rapport(self, rapport: Dict, filepath: str = None):
        """
        Sla training rapport op
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"/app/backend/training_reports/training_{timestamp}.json"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(rapport, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Rapport opgeslagen: {filepath}")
        
        return filepath


def main():
    """
    Main training function
    """
    print("🎓 Spark Conversation Trainer")
    print("=" * 60)
    
    trainer = ConversationTrainer()
    
    # Run training sessie
    rapport = trainer.run_training_session(
        bots=["madelief", "harry", "smith"],
        scenarios_per_bot=1,  # Start met 1 scenario per bot
        delay=1.5  # Sneller voor testing
    )
    
    # Save rapport
    trainer.save_rapport(rapport)
    
    print("\n🎉 Training complete! Spark heeft nu meer context en snaps.")
    print("💡 TIP: Run dit script regelmatig om Spark te blijven trainen.")


if __name__ == "__main__":
    main()
