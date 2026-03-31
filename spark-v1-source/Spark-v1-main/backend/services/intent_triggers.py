"""
Intent Triggers - Gestructureerde trigger sets voor betere herkenning
Gebruikt bestaande trigger lijsten voor synoniemen en variaties
"""
from typing import Dict, List, Set
from utils.data_manager import DataManager


class IntentTriggers:
    """
    Beheert trigger woorden per intent categorie
    Voor betere matching zonder ruis
    """
    
    # Cache voor triggers
    _triggers_cache = None
    
    @staticmethod
    def load_triggers() -> Dict[str, Set[str]]:
        """
        Laad alle trigger sets uit bestaande trigger files
        
        Returns:
            {
                "agenda": {"afspraak", "planning", "morgen", ...},
                "boekhouding": {"uitgave", "inkomen", "transactie", ...},
                "werk": {"project", "deadline", "vergadering", ...},
                ...
            }
        """
        if IntentTriggers._triggers_cache:
            return IntentTriggers._triggers_cache
        
        triggers = {}
        
        # 1. AGENDA / PLANNING (uit calendar_triggers.json)
        try:
            calendar = DataManager.load_json("triggers/calendar_triggers.json")
            agenda_words = set()
            
            # Verzamel alle relevante categorieën
            for category in ["social", "work", "personal_care", "time_indicators", "action_verbs"]:
                if category in calendar.get("triggers", {}):
                    agenda_words.update(calendar["triggers"][category])
            
            # Extra agenda-specifieke woorden
            agenda_words.update([
                "afspraak", "planning", "plan", "agenda", "kalender", "reminder",
                "herinnering", "noteer", "notitie", "inplannen", "reserveren"
            ])
            
            triggers["agenda"] = agenda_words
            
        except Exception as e:
            print(f"[TRIGGERS] Could not load calendar triggers: {e}")
            triggers["agenda"] = set()
        
        # 2. BOEKHOUDING / FINANCIËN (custom lijst)
        triggers["boekhouding"] = {
            # Basis woorden
            "boekhouding", "kasboek", "financiën", "financieel",
            
            # Transacties
            "transactie", "betaling", "betalen", "betaald", "uitgave", "inkomen",
            "ontvangst", "factuur", "nota", "bon", "rekening",
            
            # Acties
            "registreren", "registratie", "vastleggen", "bijhouden", "noteren",
            "boeken", "administreren", "verwerken",
            
            # Geld
            "euro", "geld", "bedrag", "kosten", "prijs", "tarief",
            "inkomsten", "uitgaven", "saldo", "balans",
            
            # Types
            "verkoop", "aankoop", "inkoop", "omzet", "winst", "verlies"
        }
        
        # 2A. UITGAVEN (specifieke triggers voor expense tracking)
        triggers["uitgaven"] = {
            "uitgave", "uitgegeven", "uitgeven", "betaald", "betalen",
            "gekost", "kosten", "kost", "kwijt", "euro", "€",
            "boodschappen", "eten", "drinken", "transport", "benzine",
            "huur", "gas", "licht", "water", "verzekering",
            "telefoon", "internet", "abonnement", "kleding"
        }
        
        # 2B. INKOMSTEN (specifieke triggers voor income tracking)
        triggers["inkomsten"] = {
            "inkomsten", "inkomen", "verdiend", "verdienen",
            "ontvangen", "gekregen", "kreeg", "binnen", "betaling",
            "salaris", "loon", "opdracht", "project", "bonus",
            "freelance", "factuur", "honorarium", "omzet"
        }
        
        # 2C. DAGBOEK (specifieke triggers voor journal entries)
        triggers["dagboek"] = {
            "dagboek", "schrijven", "opschrijven", "noteren",
            "entry", "notitie", "reflectie", "gedachten", "gevoel",
            "vandaag", "dag", "avond", "gebeurd", "meegemaakt",
            "blij", "verdrietig", "moe", "enthousiast", "boos"
        }
        
        # 3. WERK / PROJECTEN (uit calendar_triggers work category)
        try:
            calendar = DataManager.load_json("triggers/calendar_triggers.json")
            werk_words = set(calendar.get("triggers", {}).get("work", []))
            
            # Extra werk woorden
            werk_words.update([
                "taak", "opdracht", "assignment", "deliverable", "milestone",
                "sprint", "scrum", "stand-up", "retrospective", "review",
                "samenwerken", "samenwerking", "team", "collaboration"
            ])
            
            triggers["werk"] = werk_words
            
        except Exception:
            triggers["werk"] = {"werk", "project", "taak", "deadline"}
        
        # 4. HUISHOUDEN (uit calendar_triggers household)
        try:
            calendar = DataManager.load_json("triggers/calendar_triggers.json")
            triggers["huishouden"] = set(calendar.get("triggers", {}).get("household", []))
        except Exception:
            triggers["huishouden"] = {"opruimen", "schoonmaken", "huishouden"}
        
        # 5. BOODSCHAPPEN (uit calendar_triggers shopping)
        try:
            calendar = DataManager.load_json("triggers/calendar_triggers.json")
            triggers["boodschappen"] = set(calendar.get("triggers", {}).get("shopping", []))
        except Exception:
            triggers["boodschappen"] = {"boodschappen", "winkelen", "supermarkt"}
        
        # Cache
        IntentTriggers._triggers_cache = triggers
        
        return triggers
    
    @staticmethod
    def get_intent_score(message: str, intent: str) -> int:
        """
        Bereken score voor een intent op basis van triggers
        
        Args:
            message: De user input
            intent: De intent ("agenda", "boekhouding", etc.)
        
        Returns:
            Score (aantal matches)
        """
        triggers = IntentTriggers.load_triggers()
        
        if intent not in triggers:
            return 0
        
        message_lower = message.lower()
        intent_triggers = triggers[intent]
        
        # Tel aantal matches
        score = 0
        for trigger in intent_triggers:
            if trigger in message_lower:
                score += 1
        
        return score
    
    @staticmethod
    def detect_intent(message: str, min_score: int = 2) -> List[tuple]:
        """
        Detecteer intents in een message
        
        Args:
            message: User input
            min_score: Minimum score voor een match
        
        Returns:
            List van (intent, score) tuples, gesorteerd op score
        """
        triggers = IntentTriggers.load_triggers()
        results = []
        
        for intent in triggers.keys():
            score = IntentTriggers.get_intent_score(message, intent)
            if score >= min_score:
                results.append((intent, score))
        
        # Sorteer op score (hoogste eerst)
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    @staticmethod
    def get_triggers_for_intent(intent: str) -> Set[str]:
        """
        Haal alle trigger woorden op voor een intent
        
        Gebruik dit voor synoniem matching bij kenniskaarten
        """
        triggers = IntentTriggers.load_triggers()
        return triggers.get(intent, set())
