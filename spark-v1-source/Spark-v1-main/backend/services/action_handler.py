"""
Action Handler Service (Core)
==================================
Voert acties uit op basis van action triggers

Type: action → doet iets (create_task, create_note, etc.)
Type: response → alleen tekst

Willem's filosofie: Eerst werkend, dan slim
"""

import re
import logging
from typing import Dict, Optional

# Import services
from services.task_service import create_task
from services.notes_service import NotesService
from services.monitoring_service import get_monitoring_service

logger = logging.getLogger(__name__)


class ActionHandler:
    """
    Voert acties uit op basis van triggers
    
    Acties:
    - create_task: Maak een nieuwe taak aan
    - create_note: Maak een nieuwe notitie aan
    - start_monitor: Start monitoring service
    - stop_monitor: Stop monitoring service
    - pause_monitor: Pause/resume monitoring service
    """
    
    def __init__(self):
        logger.info("⚙️ Action Handler initialized")
    
    def execute_action(self, action: str, user_input: str, response_config: dict, user_id: str = None) -> Dict:
        """
        Voer een actie uit
        
        Args:
            action: De actie naam (bijv. "create_task", "create_note")
            user_input: De originele user input
            response_config: De response config uit de trigger card
            user_id: User ID (voor notes, optioneel)
        
        Returns:
            {
                "success": bool,
                "message": str,
                "data": dict (optional)
            }
        """
        logger.info(f"⚙️ Executing action: {action}")
        logger.info(f"   User input: {user_input}")
        
        if action == "create_task":
            return self._handle_create_task(user_input, response_config)
        
        if action == "create_note":
            return self._handle_create_note(user_input, response_config, user_id)
        
        # Monitoring actions
        if action == "start_monitor":
            return self._handle_start_monitor(response_config)
        
        if action == "stop_monitor":
            return self._handle_stop_monitor(response_config)
        
        if action == "pause_monitor":
            return self._handle_pause_monitor(response_config)
        
        # Onbekende actie
        logger.warning(f"⚠️ Unknown action: {action}")
        return {
            "success": False,
            "message": f"Actie '{action}' is niet geïmplementeerd.",
            "data": None
        }
    
    def _handle_create_task(self, user_input: str, response_config: dict) -> Dict:
        """
        Maak een nieuwe taak aan via chat
        
        Extract task text uit user input en maak task aan
        
        Voorbeelden:
        - "noteer dat ik boodschappen moet doen" → "ik boodschappen moet doen"
        - "onthoud dat morgen vergadering" → "morgen vergadering"
        - "maak taak rapport schrijven" → "rapport schrijven"
        """
        # Extract task text
        task_text = self._extract_task_text(user_input, response_config)
        
        if not task_text:
            logger.warning("⚠️ Could not extract task text from input")
            return {
                "success": False,
                "message": "Ik kon geen taak tekst herkennen. Probeer: 'noteer dat [taak]'",
                "data": None
            }
        
        # Create task (default priority: medium)
        try:
            task = create_task(task_text, priority="medium")
            
            # Get confirmation message template
            confirmation_template = response_config.get('confirmation', '✅ Taak aangemaakt: {task}')
            confirmation_message = confirmation_template.format(task=task_text)
            
            logger.info(f"✅ Task created: {task['id']}")
            
            return {
                "success": True,
                "message": confirmation_message,
                "data": {
                    "task_id": task['id'],
                    "task_text": task_text,
                    "priority": task['priority'],
                    "status": task['status']
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Error creating task: {e}")
            return {
                "success": False,
                "message": f"Er ging iets mis bij het aanmaken van de taak: {str(e)}",
                "data": None
            }
    
    def _extract_task_text(self, user_input: str, response_config: dict) -> Optional[str]:
        """
        Extract de task tekst uit user input
        
        Strategie:
        1. Probeer trigger pattern te gebruiken
        2. Fallback: strip bekende trigger woorden
        
        Returns:
            De task tekst of None
        """
        user_lower = user_input.lower().strip()
        
        # Bekende prefixes om te strippen
        prefixes_to_remove = [
            "noteer dat ",
            "noteer ",
            "onthoud dat ",
            "onthoud ",
            "maak taak ",
            "maak een taak ",
            "nieuwe taak ",
            "taak "
        ]
        
        # Probeer elke prefix te strippen
        for prefix in prefixes_to_remove:
            if user_lower.startswith(prefix):
                task_text = user_input[len(prefix):].strip()
                
                # Valideer dat er nog tekst over is
                if task_text and len(task_text) > 0:
                    return task_text
        
        # Geen match gevonden
        return None
    
    def _handle_create_note(self, user_input: str, response_config: dict, user_id: str = None) -> Dict:
        """
        Maak een nieuwe notitie aan via chat
        
        Extract titel en inhoud uit user input
        
        Voorbeelden:
        - "schrijf notitie over BCH strategie" → titel: "BCH strategie", inhoud: user_input
        - "schrijf notitie: vandaag een inzicht gehad" → titel: "Inzicht", inhoud: user_input
        """
        if not user_id:
            return {
                "success": False,
                "message": "Je moet ingelogd zijn om een notitie te maken",
                "data": None
            }
        
        # Extract titel uit user input
        titel, inhoud = self._extract_note_content(user_input, response_config)
        
        if not titel:
            return {
                "success": False,
                "message": "Ik kon geen titel herkennen. Probeer: 'schrijf notitie over [onderwerp]'",
                "data": None
            }
        
        # Create note
        try:
            note = NotesService.add_note(
                user_id=user_id,
                titel=titel,
                inhoud=inhoud,
                categorie="Algemeen",  # Default category
                tags=[],
                created_by="Chat Trigger"
            )
            
            # Get confirmation message
            confirmation_template = response_config.get('confirmation', '✅ Notitie aangemaakt: {titel}')
            confirmation_message = confirmation_template.format(titel=titel)
            
            logger.info(f"✅ Note created: {note['id']}")
            
            return {
                "success": True,
                "message": confirmation_message,
                "data": {
                    "note_id": note['id'],
                    "titel": titel,
                    "inhoud": inhoud
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Error creating note: {e}")
            return {
                "success": False,
                "message": f"Er ging iets mis bij het aanmaken van de notitie: {str(e)}",
                "data": None
            }
    
    def _extract_note_content(self, user_input: str, response_config: dict) -> tuple:
        """
        Extract titel en inhoud uit user input
        
        Returns:
            (titel, inhoud)
        """
        user_lower = user_input.lower().strip()
        
        # Bekende prefixes voor note triggers
        prefixes_to_remove = [
            "schrijf notitie over ",
            "schrijf notitie: ",
            "schrijf notitie ",
            "maak notitie over ",
            "maak notitie: ",
            "maak notitie ",
            "noteer dit: "
        ]
        
        # Probeer elke prefix te strippen
        for prefix in prefixes_to_remove:
            if user_lower.startswith(prefix):
                rest = user_input[len(prefix):].strip()
                
                if rest:
                    # Titel = eerste 50 chars (of tot eerste punt/newline)
                    titel = rest.split('\n')[0].split('.')[0][:50].strip()
                    inhoud = rest
                    
                    return (titel, inhoud)
        
        # Geen match
        return (None, None)
    
    def _handle_start_monitor(self, response_config: dict) -> Dict:
        """
        Start monitoring service
        
        Default interval: 3600 sec (1 uur candle) voor trading
        """
        try:
            monitoring_service = get_monitoring_service()
            # Start met 1 uur interval (trading candle)
            result = monitoring_service.start(interval=3600)
            
            return {
                "success": result['success'],
                "message": result['message'],
                "data": result.get('status')
            }
        except Exception as e:
            logger.error(f"❌ Error starting monitor: {e}")
            return {
                "success": False,
                "message": f"Kon monitor niet starten: {str(e)}",
                "data": None
            }
    
    def _handle_stop_monitor(self, response_config: dict) -> Dict:
        """Stop monitoring service"""
        try:
            monitoring_service = get_monitoring_service()
            result = monitoring_service.stop()
            
            return {
                "success": result['success'],
                "message": result['message'],
                "data": result.get('status')
            }
        except Exception as e:
            logger.error(f"❌ Error stopping monitor: {e}")
            return {
                "success": False,
                "message": f"Kon monitor niet stoppen: {str(e)}",
                "data": None
            }
    
    def _handle_pause_monitor(self, response_config: dict) -> Dict:
        """Pause/resume monitoring service"""
        try:
            monitoring_service = get_monitoring_service()
            result = monitoring_service.pause()
            
            return {
                "success": result['success'],
                "message": result['message'],
                "data": result.get('status')
            }
        except Exception as e:
            logger.error(f"❌ Error pausing monitor: {e}")
            return {
                "success": False,
                "message": f"Kon monitor niet pauzeren: {str(e)}",
                "data": None
            }


# Singleton instance
_action_handler = None

def get_action_handler():
    """Get singleton action handler"""
    global _action_handler
    if _action_handler is None:
        _action_handler = ActionHandler()
    return _action_handler


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    handler = ActionHandler()
    
    print("=" * 60)
    print("🧪 TEST ACTION HANDLER")
    print("=" * 60)
    
    test_inputs = [
        ("noteer dat ik boodschappen moet doen", {"confirmation": "✅ Genoteerd: {task}"}),
        ("onthoud dat morgen vergadering", {"confirmation": "✅ Onthouden: {task}"}),
        ("maak taak rapport schrijven", {"confirmation": "✅ Taak aangemaakt: {task}"}),
        ("noteer", {"confirmation": "✅ Genoteerd: {task}"}),  # Foutief (geen tekst)
    ]
    
    for user_input, response_config in test_inputs:
        print(f"\n📝 Input: '{user_input}'")
        result = handler.execute_action("create_task", user_input, response_config)
        
        if result['success']:
            print("   ✅ SUCCESS")
            print(f"   Message: {result['message']}")
            print(f"   Task ID: {result['data'].get('task_id')}")
        else:
            print("   ❌ FAILED")
            print(f"   Message: {result['message']}")
    
    print("\n" + "=" * 60)
