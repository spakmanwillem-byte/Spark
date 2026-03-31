"""
Trigger Manager Service - Self-service admin tool voor trigger lijst beheer

Willem kan zelf trigger woorden toevoegen aan:
- Emotie triggers (blij, boos, bang, bedroefd)
- Stopwoorden
- (Toekomstige lijsten)

Dit bespaart credits omdat Willem het zelf kan doen zonder agent hulp.
"""
from typing import Dict, List, Optional, Tuple
from utils.data_manager import DataManager
import json


class TriggerManagerService:
    """Service voor het beheren van trigger lijsten via admin commands"""
    
    @staticmethod
    def get_available_lists() -> Dict:
        """
        Get available trigger lists for admin menu
        
        Returns:
            {
                "a": {"name": "Emotie: Blij", "type": "emotion", "emotion": "blij"},
                "b": {"name": "Emotie: Boos", "type": "emotion", "emotion": "boos"},
                ...
            }
        """
        return {
            "a": {
                "name": "Emotie: Blij 😊",
                "type": "emotion",
                "emotion": "blij",
                "file": "triggers/emotion_triggers.json",
                "path": ["emotions", "blij", "triggers"]
            },
            "b": {
                "name": "Emotie: Boos 😠",
                "type": "emotion",
                "emotion": "boos",
                "file": "triggers/emotion_triggers.json",
                "path": ["emotions", "boos", "triggers"]
            },
            "c": {
                "name": "Emotie: Bang 😰",
                "type": "emotion",
                "emotion": "bang",
                "file": "triggers/emotion_triggers.json",
                "path": ["emotions", "bang", "triggers"]
            },
            "d": {
                "name": "Emotie: Bedroefd 😢",
                "type": "emotion",
                "emotion": "bedroefd",
                "file": "triggers/emotion_triggers.json",
                "path": ["emotions", "bedroefd", "triggers"]
            }
        }
    
    @staticmethod
    def get_list_menu_text() -> str:
        """Generate menu text for available lists"""
        lists = TriggerManagerService.get_available_lists()
        
        menu_text = "**Trigger Lijsten Beheer** 🎛️\n\n"
        menu_text += "Kies een lijst om woorden aan toe te voegen:\n\n"
        
        for key, info in lists.items():
            menu_text += f"{key}) {info['name']}\n"
        
        menu_text += "\nType de letter van je keuze (of 'stop' om te annuleren)"
        
        return menu_text
    
    @staticmethod
    def add_words_to_trigger_list(list_key: str, words: List[str], default_score: int = 3) -> Tuple[bool, str]:
        """
        Add words to a trigger list
        
        Args:
            list_key: "a", "b", "c", "d", etc.
            words: List of words to add
            default_score: Default score for new words (default: 3)
            
        Returns:
            (success: bool, message: str)
        """
        lists = TriggerManagerService.get_available_lists()
        
        if list_key not in lists:
            return False, f"Ongeldige lijst keuze: {list_key}"
        
        list_info = lists[list_key]
        file_path = list_info["file"]
        json_path = list_info["path"]
        
        try:
            # Load JSON file
            data = DataManager.load_json(file_path)
            
            # Navigate to the correct nested path
            current = data
            for key in json_path[:-1]:
                current = current[key]
            
            # Get the triggers dict (last item in path)
            triggers_key = json_path[-1]
            triggers = current.get(triggers_key, {})
            
            # Add new words
            added = []
            skipped = []
            
            for word in words:
                word_clean = word.strip().lower()
                if not word_clean:
                    continue
                
                if word_clean in triggers:
                    skipped.append(word_clean)
                else:
                    triggers[word_clean] = default_score
                    added.append(word_clean)
            
            # Update data
            current[triggers_key] = triggers
            
            # Save back to file
            DataManager.save_json(file_path, data)
            
            # Build result message
            result_msg = f"✅ **Trigger lijst bijgewerkt: {list_info['name']}**\n\n"
            
            if added:
                result_msg += f"**Toegevoegd ({len(added)}):**\n"
                result_msg += ", ".join(added) + "\n\n"
            
            if skipped:
                result_msg += f"**Overgeslagen (bestonden al):**\n"
                result_msg += ", ".join(skipped) + "\n\n"
            
            result_msg += f"💡 Tip: Emotie triggers werken direct (cache: 60 sec)"
            
            return True, result_msg
            
        except Exception as e:
            return False, f"❌ Fout bij bijwerken lijst: {str(e)}"
    
    @staticmethod
    def get_current_triggers(list_key: str) -> Tuple[bool, List[str]]:
        """
        Get current triggers in a list
        
        Returns:
            (success: bool, triggers: List[str])
        """
        lists = TriggerManagerService.get_available_lists()
        
        if list_key not in lists:
            return False, []
        
        list_info = lists[list_key]
        file_path = list_info["file"]
        json_path = list_info["path"]
        
        try:
            data = DataManager.load_json(file_path)
            
            # Navigate to triggers
            current = data
            for key in json_path[:-1]:
                current = current[key]
            
            triggers = current.get(json_path[-1], {})
            
            return True, list(triggers.keys())
            
        except Exception as e:
            return False, []
    
    @staticmethod
    def view_trigger_list(list_key: str) -> Tuple[bool, str]:
        """
        View all words in a trigger list with scores
        
        Returns:
            (success: bool, formatted_output: str)
        """
        lists = TriggerManagerService.get_available_lists()
        
        if list_key not in lists:
            return False, f"Ongeldige lijst: {list_key}"
        
        list_info = lists[list_key]
        
        try:
            data = DataManager.load_json(list_info["file"])
            
            # Navigate to triggers
            current = data
            for key in list_info["path"][:-1]:
                current = current[key]
            
            triggers = current.get(list_info["path"][-1], {})
            
            # Format output
            output = f"**{list_info['name']}**\n\n"
            output += f"Totaal: {len(triggers)} woorden\n\n"
            
            # Sort by score (high to low), then alphabetically
            sorted_triggers = sorted(triggers.items(), key=lambda x: (-x[1], x[0]))
            
            for word, score in sorted_triggers:
                output += f"• {word} (score: {score})\n"
            
            return True, output
            
        except Exception as e:
            return False, f"Fout bij ophalen lijst: {str(e)}"
    
    @staticmethod
    def move_word(word: str, from_list: str, to_list: str) -> Tuple[bool, str]:
        """
        Move a word from one emotion list to another
        
        Returns:
            (success: bool, message: str)
        """
        lists = TriggerManagerService.get_available_lists()
        
        if from_list not in lists or to_list not in lists:
            return False, "Ongeldige lijst specificatie"
        
        from_info = lists[from_list]
        to_info = lists[to_list]
        
        # Both must be same file (emotions)
        if from_info["file"] != to_info["file"]:
            return False, "Kan alleen binnen hetzelfde bestand verplaatsen"
        
        try:
            data = DataManager.load_json(from_info["file"])
            
            # Get source triggers
            current = data
            for key in from_info["path"][:-1]:
                current = current[key]
            source_triggers = current.get(from_info["path"][-1], {})
            
            # Get target triggers
            current = data
            for key in to_info["path"][:-1]:
                current = current[key]
            target_triggers = current.get(to_info["path"][-1], {})
            
            # Check if word exists in source
            if word not in source_triggers:
                return False, f"Woord '{word}' niet gevonden in {from_info['name']}"
            
            # Move word
            score = source_triggers[word]
            target_triggers[word] = score
            del source_triggers[word]
            
            # Save
            DataManager.save_json(from_info["file"], data)
            
            return True, f"✅ '{word}' verplaatst van {from_info['name']} naar {to_info['name']}"
            
        except Exception as e:
            return False, f"Fout: {str(e)}"
    
    @staticmethod
    def remove_word(word: str, list_key: str) -> Tuple[bool, str]:
        """
        Remove a word from a trigger list
        
        Returns:
            (success: bool, message: str)
        """
        lists = TriggerManagerService.get_available_lists()
        
        if list_key not in lists:
            return False, f"Ongeldige lijst: {list_key}"
        
        list_info = lists[list_key]
        
        try:
            data = DataManager.load_json(list_info["file"])
            
            # Navigate to triggers
            current = data
            for key in list_info["path"][:-1]:
                current = current[key]
            
            triggers = current.get(list_info["path"][-1], {})
            
            if word not in triggers:
                return False, f"Woord '{word}' niet gevonden in {list_info['name']}"
            
            # Remove word
            del triggers[word]
            
            # Save
            DataManager.save_json(list_info["file"], data)
            
            return True, f"✅ '{word}' verwijderd uit {list_info['name']}"
            
        except Exception as e:
            return False, f"Fout: {str(e)}"
    
    @staticmethod
    def format_triggers_display(list_key: str) -> str:
        """Format current triggers for display"""
        lists = TriggerManagerService.get_available_lists()
        
        if list_key not in lists:
            return "Ongeldige lijst"
        
        list_info = lists[list_key]
        success, triggers = TriggerManagerService.get_current_triggers(list_key)
        
        if not success:
            return f"❌ Kon triggers niet laden voor {list_info['name']}"
        
        result = f"**{list_info['name']}**\n\n"
        result += f"Huidige triggers ({len(triggers)}):\n"
        result += ", ".join(sorted(triggers))
        
        return result
