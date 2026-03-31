"""
Chat Action Handler - Verwerk acties uit chat naar Fase 1 modules
Parse en sla data op voor Uitgaven, Inkomsten en Dagboek
"""
from typing import Dict, Optional, Tuple
import re
from datetime import datetime
from services.dagboek_service import DagboekService
from utils.data_manager import DataManager


class ChatActionHandler:
    """
    Verwerkt chat acties naar de juiste modules
    """
    
    @staticmethod
    def detect_action_type(message: str) -> Optional[str]:
        """
        Detecteer welk type actie de user wil uitvoeren
        
        Returns:
            "expense", "income", "dagboek" of None
        """
        message_lower = message.lower()
        
        # Check uitgave triggers
        expense_triggers = ["uitgave", "uitgegeven", "betaald", "gekost", "kwijt", "€"]
        if any(trigger in message_lower for trigger in expense_triggers):
            return "expense"
        
        # Check inkomsten triggers
        income_triggers = ["inkomsten", "verdiend", "ontvangen", "binnen", "gekregen"]
        if any(trigger in message_lower for trigger in income_triggers):
            return "income"
        
        # Check dagboek triggers
        dagboek_triggers = ["dagboek", "schrijven", "opschrijven", "entry", "reflectie"]
        if any(trigger in message_lower for trigger in dagboek_triggers):
            return "dagboek"
        
        return None
    
    @staticmethod
    def parse_expense(message: str) -> Optional[Dict]:
        """
        Parse uitgave informatie uit een chat bericht
        
        Returns:
            {
                "amount": float,
                "description": str,
                "category": str (optioneel)
            }
        """
        # Extract bedrag (€20, 20 euro, 20,50)
        amount_match = re.search(r'[€$]?\s*(\d+(?:[,.]\d{1,2})?)\s*(?:euro)?', message, re.IGNORECASE)
        if not amount_match:
            return None
        
        amount = float(amount_match.group(1).replace(',', '.'))
        
        # Extract beschrijving (woorden na "voor", "aan", "bij")
        description = ""
        desc_match = re.search(r'(?:voor|aan|bij|van)\s+(.+?)(?:\.|$)', message, re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip()
        else:
            # Fallback: neem alles na het bedrag
            description_parts = message.split(str(amount_match.group(0)))
            if len(description_parts) > 1:
                description = description_parts[1].strip()
        
        # Detecteer category op basis van keywords
        message_lower = message.lower()
        category = "overig"
        
        if any(word in message_lower for word in ["boodschappen", "eten", "supermarkt"]):
            category = "boodschappen"
        elif any(word in message_lower for word in ["benzine", "transport", "trein", "bus"]):
            category = "transport"
        elif any(word in message_lower for word in ["netflix", "spotify", "abonnement"]):
            category = "abonnementen"
        elif any(word in message_lower for word in ["kleding", "schoenen"]):
            category = "kleding"
        elif any(word in message_lower for word in ["restaurant", "uit eten", "lunch", "diner"]):
            category = "uit eten"
        
        return {
            "amount": amount,
            "description": description or "Uitgave via chat",
            "category": category
        }
    
    @staticmethod
    def parse_income(message: str) -> Optional[Dict]:
        """
        Parse inkomsten informatie uit een chat bericht
        """
        # Extract bedrag
        amount_match = re.search(r'[€$]?\s*(\d+(?:[,.]\d{1,2})?)\s*(?:euro)?', message, re.IGNORECASE)
        if not amount_match:
            return None
        
        amount = float(amount_match.group(1).replace(',', '.'))
        
        # Extract beschrijving
        description = ""
        desc_match = re.search(r'(?:voor|van|met|uit)\s+(.+?)(?:\.|$)', message, re.IGNORECASE)
        if desc_match:
            description = desc_match.group(1).strip()
        else:
            description_parts = message.split(str(amount_match.group(0)))
            if len(description_parts) > 1:
                description = description_parts[1].strip()
        
        # Detecteer category
        message_lower = message.lower()
        category = "overig"
        
        if any(word in message_lower for word in ["salaris", "loon", "betaling"]):
            category = "salaris"
        elif any(word in message_lower for word in ["opdracht", "project", "freelance"]):
            category = "freelance"
        elif any(word in message_lower for word in ["verkoop", "verkocht"]):
            category = "verkoop"
        
        return {
            "amount": amount,
            "description": description or "Inkomsten via chat",
            "category": category
        }
    
    @staticmethod
    def parse_dagboek(message: str) -> Optional[Dict]:
        """
        Parse dagboek entry uit een chat bericht
        """
        # Verwijder de trigger woorden voor de content
        content = message
        triggers = ["dagboek", "schrijven", "opschrijven", "entry", "reflectie", "noteren"]
        for trigger in triggers:
            content = re.sub(rf'\b{trigger}\b:?\s*', '', content, flags=re.IGNORECASE)
        
        content = content.strip()
        
        if not content or len(content) < 10:
            return None
        
        # Detecteer mood uit de tekst
        mood = None
        mood_keywords = {
            "blij": "blij",
            "happy": "blij",
            "verdrietig": "verdrietig",
            "sad": "verdrietig",
            "moe": "moe",
            "tired": "moe",
            "boos": "boos",
            "angry": "boos",
            "enthousiast": "enthousiast",
            "energiek": "energiek",
            "gespannen": "gespannen",
            "stressed": "gespannen"
        }
        
        content_lower = content.lower()
        for keyword, mood_value in mood_keywords.items():
            if keyword in content_lower:
                mood = mood_value
                break
        
        return {
            "content": content,
            "mood": mood,
            "tags": []  # Kan later uitgebreid worden
        }
    
    @staticmethod
    def save_expense(user_id: str, expense_data: Dict) -> Tuple[bool, str]:
        """
        Sla uitgave op
        
        Returns:
            (success, message)
        """
        try:
            # Load user expenses
            file_path = f"users/{user_id}/expenses.json"
            expenses_data = DataManager.load_data(file_path)
            
            # Ensure it's a list
            if not isinstance(expenses_data, list):
                expenses_data = []
            
            # Create new expense
            import uuid
            new_expense = {
                "id": str(uuid.uuid4()),
                "date": datetime.now().isoformat(),
                "amount": expense_data["amount"],
                "category": expense_data.get("category", "overig"),
                "description": expense_data["description"]
            }
            
            expenses_data.append(new_expense)
            DataManager.save_data(file_path, expenses_data)
            
            return True, f"✅ Uitgave van €{expense_data['amount']:.2f} geregistreerd voor {expense_data['category']}."
        
        except Exception as e:
            print(f"[EXPENSE SAVE ERROR] {str(e)}")
            return False, "❌ Kon uitgave niet opslaan."
    
    @staticmethod
    def save_income(user_id: str, income_data: Dict) -> Tuple[bool, str]:
        """
        Sla inkomsten op
        
        Returns:
            (success, message)
        """
        try:
            file_path = f"users/{user_id}/income.json"
            income_list = DataManager.load_data(file_path)
            
            # Ensure it's a list
            if not isinstance(income_list, list):
                income_list = []
            
            import uuid
            new_income = {
                "id": str(uuid.uuid4()),
                "date": datetime.now().isoformat(),
                "amount": income_data["amount"],
                "category": income_data.get("category", "overig"),
                "description": income_data["description"]
            }
            
            income_list.append(new_income)
            DataManager.save_data(file_path, income_list)
            
            return True, f"✅ Inkomsten van €{income_data['amount']:.2f} geregistreerd voor {income_data['category']}."
        
        except Exception as e:
            print(f"[INCOME SAVE ERROR] {str(e)}")
            return False, "❌ Kon inkomsten niet opslaan."
    
    @staticmethod
    def save_dagboek(user_id: str, dagboek_data: Dict) -> Tuple[bool, str]:
        """
        Sla dagboek entry op
        
        Returns:
            (success, message)
        """
        try:
            DagboekService.add_entry(
                user_id=user_id,
                content=dagboek_data["content"],
                mood=dagboek_data.get("mood"),
                tags=dagboek_data.get("tags", [])
            )
            
            mood_emoji = {
                "blij": "😊",
                "verdrietig": "😢",
                "moe": "😴",
                "boos": "😠",
                "enthousiast": "🎉",
                "energiek": "⚡",
                "gespannen": "😰"
            }
            
            mood_str = f" ({mood_emoji.get(dagboek_data['mood'], '')})" if dagboek_data.get('mood') else ""
            return True, f"✅ Dagboek entry opgeslagen{mood_str}."
        
        except Exception as e:
            print(f"[DAGBOEK SAVE ERROR] {str(e)}")
            return False, "❌ Kon dagboek entry niet opslaan."
    
    @staticmethod
    def handle_chat_action(message: str, user_id: str) -> Optional[Tuple[bool, str]]:
        """
        Main handler - detecteer en verwerk actie
        
        Returns:
            (success, response_message) of None als geen actie gedetecteerd
        """
        action_type = ChatActionHandler.detect_action_type(message)
        
        if not action_type:
            return None
        
        if action_type == "expense":
            expense_data = ChatActionHandler.parse_expense(message)
            if expense_data:
                return ChatActionHandler.save_expense(user_id, expense_data)
            else:
                return False, "Ik kon het bedrag niet herkennen. Probeer iets als: 'ik heb €20 uitgegeven aan boodschappen'"
        
        elif action_type == "income":
            income_data = ChatActionHandler.parse_income(message)
            if income_data:
                return ChatActionHandler.save_income(user_id, income_data)
            else:
                return False, "Ik kon het bedrag niet herkennen. Probeer iets als: 'ik heb €50 verdiend met een opdracht'"
        
        elif action_type == "dagboek":
            dagboek_data = ChatActionHandler.parse_dagboek(message)
            if dagboek_data:
                return ChatActionHandler.save_dagboek(user_id, dagboek_data)
            else:
                return False, "Ik kon de dagboek tekst niet herkennen. Probeer iets als: 'dagboek: vandaag was een goede dag'"
        
        return None
