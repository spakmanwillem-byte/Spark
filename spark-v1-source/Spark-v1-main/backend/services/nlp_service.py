import re
import spacy
from typing import Optional, Dict, Tuple
from Levenshtein import distance as levenshtein_distance
from utils.data_manager import DataManager

class NLPService:
    def __init__(self):
        # Lazy loading: don't load spaCy model during __init__
        self._nlp = None
        
        # Load keywords
        self.keywords = DataManager.load_json("system/keywords.json")
        
        # Load conversation triggers (NEW)
        self.conversation_triggers = DataManager.load_json("triggers/conversation_triggers.json")
    
    @property
    def nlp(self):
        """Lazy load spaCy model only when first accessed"""
        if self._nlp is None:
            try:
                self._nlp = spacy.load("nl_core_news_sm")
            except Exception as e:
                print(f"Warning: Failed to load spaCy model: {e}")
                self._nlp = False  # Mark as failed
        return self._nlp if self._nlp is not False else None
    
    def extract_identification(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extract naam, volledige_naam, sleutelwoord or masterkey from natural language
        
        Patterns:
        - "Ik ben [naam] ([volledige naam]) en mijn sleutelwoord is [woord]"
        - "Ik ben [naam], sleutelwoord [woord]"
        - "Ik ben [naam] ([volledige naam]) mijn Masterkey is Samen"
        - "Hallo ik ben [naam] en mijn sleutelwoord is [woord]"
        - "[naam] [sleutelwoord]" (simple: "Willem Appelsap")
        - "[naam] Masterkey [word]" (simple: "Willem Masterkey Samen")
        
        NOTE: This should NOT trigger on phrases like "Ik ben blij" or "Ik ben moe"
        """
        result = {}
        text_lower = text.lower()
        
        # Blacklist: common words that should NOT be interpreted as names
        # (emotions, states, adjectives, common responses)
        COMMON_WORDS_BLACKLIST = [
            "blij", "boos", "verdrietig", "bang", "moe", "wakker", "klaar", 
            "terug", "weg", "hier", "daar", "zo", "er", "aan", "uit",
            "goed", "slecht", "ok", "oké", "okay", "prima", "top",
            "bezig", "druk", "vrij", "alleen", "samen", "thuis"
        ]
        
        # Check for Masterkey first (case insensitive)
        masterkey_patterns = [
            r"(?:mijn\s+)?masterkey\s+is\s+(\w+)",
            r"masterkey[:\s]+(\w+)",
            r"masterkey\s+(\w+)"
        ]
        for pattern in masterkey_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                masterkey = match.group(1)
                if masterkey.lower() == "samen":
                    result["masterkey"] = "SAMEN"
        
        # Extract sleutelwoord
        sleutelwoord_patterns = [
            r"(?:mijn\s+)?sleutelwoord\s+is\s+(\w+)",
            r"sleutelwoord[:\s]+(\w+)",
            r"sleutelwoord\s+(\w+)",
            # NEW: Support "Ik ben [naam], [sleutelwoord]" pattern (multi-word names)
            r"ik\s+ben\s+((?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)),\s*(\w+)"
        ]
        
        # PRIORITY PATTERN: "Ik ben [Voornaam Achternaam] Sleutelwoord: [woord]"
        # This handles: "Ik ben Willem Spakman Sleutelwoord: Appelsap"
        sleutelwoord_separator_pattern = r"ik\s+ben\s+((?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))\s+[Ss]leutelwoord\s*[:=]?\s*([A-Z][a-zA-Z0-9]+)"
        sep_match = re.search(sleutelwoord_separator_pattern, text, re.IGNORECASE)
        if sep_match:
            volledige_naam = sep_match.group(1).strip()
            sleutelwoord = sep_match.group(2).strip()
            naam_parts = volledige_naam.split()
            
            # Check if not blacklisted
            if naam_parts[0].lower() not in COMMON_WORDS_BLACKLIST:
                result["naam"] = naam_parts[0]
                result["volledige_naam"] = volledige_naam
                result["sleutelwoord"] = sleutelwoord
                print(f"[NLP] Extracted via Sleutelwoord separator: {volledige_naam}, {sleutelwoord}")
                return result if result else None
        
        # Check comma-separated pattern (original)
        # "Ik ben [Voornaam Achternaam], [sleutelwoord]"
        comma_match = re.search(r"ik\s+ben\s+((?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)),\s*(\w+)", text, re.IGNORECASE)
        if comma_match:
            naam_part = comma_match.group(1)
            sleutelwoord_part = comma_match.group(2)
            
            # Check if naam is not blacklisted
            COMMON_WORDS_BLACKLIST = [
                "blij", "boos", "verdrietig", "bang", "moe", "wakker", "klaar", 
                "terug", "weg", "hier", "daar", "zo", "er", "aan", "uit",
                "goed", "slecht", "ok", "oké", "okay", "prima", "top",
                "bezig", "druk", "vrij", "alleen", "samen", "thuis"
            ]
            
            # Check first word of naam against blacklist
            first_word = naam_part.split()[0].lower()
            
            if first_word not in COMMON_WORDS_BLACKLIST and len(sleutelwoord_part) > 2:
                result["naam"] = naam_part
                result["sleutelwoord"] = sleutelwoord_part
                # Skip other patterns since we found a match
                sleutelwoord_patterns = []
        
        for pattern in sleutelwoord_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Make sure we don't capture just "is"
                word = match.group(1) if len(match.groups()) == 1 else match.group(2)
                if word.lower() != "is" and len(word) > 1:
                    result["sleutelwoord"] = word
                    break
        
        # Extract naam (with optional full name in parentheses)
        # BELANGRIJK: Probeer altijd volledige naam te extraheren (voornaam + achternaam)
        naam_patterns = [
            # Pattern 1: "Ik ben [Voornaam Achternaam] en mijn sleutelwoord is [woord]"
            r"(?:ik\s+ben|mijn\s+naam\s+is|hallo\s+ik\s+ben)\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            # Pattern 2: "Ik ben [De Willem]" (lidwoord + naam)
            r"(?:ik\s+ben|mijn\s+naam\s+is|hallo\s+ik\s+ben)\s+((?:de|het)\s+[A-Z][a-z]+)",
            # Pattern 3: "Ik ben [Willem] ([Willem Spakman])" - met volledige naam in haakjes
            r"(?:ik\s+ben|mijn\s+naam\s+is|hallo\s+ik\s+ben)\s+([A-Z][a-z]+)(?:\s+\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\))?",
            # Pattern 4: Alleen voornaam (fallback, maar we vragen dan door naar achternaam)
            r"(?:ik\s+ben|mijn\s+naam\s+is)\s+([A-Z][a-z]+)(?!\s+[A-Z])"
        ]
        
        for pattern in naam_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                potential_naam = match.group(1)
                
                # Check if this is a blacklisted common word
                if potential_naam.lower() in COMMON_WORDS_BLACKLIST:
                    print(f"[NLP] Skipping identification: '{potential_naam}' is blacklisted word")
                    continue
                
                # Check if we have a full name (contains space = voornaam + achternaam)
                if ' ' in potential_naam:
                    # Full name detected (voornaam achternaam)
                    naam_parts = potential_naam.split()
                    result["naam"] = naam_parts[0]  # Voornaam
                    result["volledige_naam"] = potential_naam  # Volledige naam
                elif len(match.groups()) >= 2 and match.group(2):
                    # Format: "Ik ben Willem (Willem Spakman)"
                    result["naam"] = match.group(1)
                    result["volledige_naam"] = match.group(2)
                else:
                    # Alleen voornaam - opslaan maar volledige_naam blijft leeg
                    result["naam"] = potential_naam
                    # Geen volledige_naam - Spark zal doorvragen
                break
        
        # Simple pattern: just "[Naam] [Sleutelwoord]" or "[Naam] Masterkey [woord]"
        if not result or "naam" not in result:
            # Try simple two-word pattern
            words = text.strip().split()
            
            # Handle "login [Naam] [Sleutelwoord]" pattern
            if len(words) >= 3 and words[0].lower() == "login":
                # "login De Willem Appelsap" or "login Willem Appelsap"
                if words[1][0].isupper():
                    # Could be "De Willem" or just "Willem"
                    if words[2][0].isupper():
                        # Two uppercase words after "login"
                        if words[1].lower() in ["de", "het"]:
                            # "login De Willem Appelsap" → naam="De Willem", sleutelwoord="Appelsap"
                            if len(words) >= 4 and words[3][0].isupper():
                                result["naam"] = f"{words[1]} {words[2]}"
                                if words[3].lower() == "samen":
                                    result["masterkey"] = "SAMEN"
                                else:
                                    result["sleutelwoord"] = words[3]
                        else:
                            # "login Willem Appelsap"
                            result["naam"] = words[1]
                            if words[2].lower() == "samen":
                                result["masterkey"] = "SAMEN"
                            else:
                                result["sleutelwoord"] = words[2]
            
            # Try simple two-word pattern
            elif len(words) == 2:
                # Could be "Willem Appelsap"
                if words[0][0].isupper() and words[1][0].isupper():
                    # Check blacklist for first word
                    if words[0].lower() in COMMON_WORDS_BLACKLIST:
                        return None
                    
                    if "naam" not in result:
                        result["naam"] = words[0]
                    if words[1].lower() == "samen":
                        result["masterkey"] = "SAMEN"
                    else:
                        result["sleutelwoord"] = words[1]
            
            # Handle three words like "De Willem Appelsap"
            elif len(words) == 3:
                if words[0].lower() in ["de", "het"] and words[1][0].isupper() and words[2][0].isupper():
                    # "De Willem Appelsap"
                    result["naam"] = f"{words[0]} {words[1]}"
                    if words[2].lower() == "samen":
                        result["masterkey"] = "SAMEN"
                    else:
                        result["sleutelwoord"] = words[2]
                elif words[1].lower() == "masterkey":
                    # "Willem Masterkey Samen"
                    if "naam" not in result:
                        result["naam"] = words[0]
                    if words[2].lower() == "samen":
                        result["masterkey"] = "SAMEN"
        
        # IMPORTANT: Only return if we have STRONG evidence of identification
        # Either: (naam + sleutelwoord) OR (naam + masterkey) OR just (sleutelwoord/masterkey keyword present)
        if result:
            has_credential = "sleutelwoord" in result or "masterkey" in result
            has_naam = "naam" in result
            
            # Require at least a credential keyword OR a clear two-word pattern
            if has_credential or (has_naam and ("sleutelwoord" in text_lower or "masterkey" in text_lower)):
                return result
            
            # If only naam without any credential context, likely not identification
            if has_naam and not has_credential:
                print("[NLP] Skipping identification: naam found but no sleutelwoord/masterkey context")
                return None
        
        return None
    
    def detect_sentiment(self, text: str) -> str:
        """
        Detect sentiment: positief, negatief, or neutraal
        """
        text_lower = text.lower()
        
        positieve_woorden = self.keywords.get("emoties", {}).get("woorden", {}).get("positief", [])
        negatieve_woorden = self.keywords.get("emoties", {}).get("woorden", {}).get("negatief", [])
        
        pos_count = sum(1 for word in positieve_woorden if word in text_lower)
        neg_count = sum(1 for word in negatieve_woorden if word in text_lower)
        
        if pos_count > neg_count:
            return "positief"
        elif neg_count > pos_count:
            return "negatief"
        else:
            return "neutraal"
    
    def detect_command(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Detect commands in text
        Returns: (command_type, content)
        """
        text_lower = text.lower().strip()
        
        # Check for roadmap commands
        roadmap_triggers = ["roadmap", "wat is de roadmap", "laat roadmap zien", "planning", "wat gaan we bouwen"]
        if any(trigger in text_lower for trigger in roadmap_triggers):
            return ("roadmap", "")
        
        # Check for user/people questions
        people_triggers = ["welke gebruikers", "wie ken je", "wie kent spark", "hoeveel mensen", "wie zijn er"]
        if any(trigger in text_lower for trigger in people_triggers):
            return ("show_users", "")
        
        
        # Check for bio/identity commands
        bio_triggers = ["wie ben je", "wie ben jij", "vertel over jezelf", "wat is roadkill", "wat is spark your life", "wie is roadkill", "roadkill community", "over roadkill", "over spark your life"]
        if any(trigger in text_lower for trigger in bio_triggers):
            # Determine what they're asking about
            if "roadkill" in text_lower and "community" in text_lower:
                return ("bio_query", "roadkill_community")
            elif "roadkill" in text_lower:
                return ("bio_query", "roadkill")
            elif "spark your life" in text_lower:
                return ("bio_query", "spark_your_life")
            else:
                return ("bio_query", "general")

        # Check for help commands (IMPROVED: natural language)
        help_triggers = [
            "wat kan ik nu", "wat kan ik doen", "help", "functies", "commando's",
            "wat kan je", "mogelijkheden", "help me", "wat zijn de opties",
            "hoe werkt dit", "wat kan spark", "commands", "wat moet ik doen"
        ]
        if any(trigger in text_lower for trigger in help_triggers):
            return ("help", "")
        
        # Check for logout commands (IMPROVED: natural language)
        logout_triggers = [
            "afmelden", "uitloggen", "log uit", "logout", "afmeld",
            "ik wil uitloggen", "ik ga uitloggen", "tot ziens", "doei",
            "ik ga weg", "log me uit", "meld me af"
        ]
        if any(trigger in text_lower for trigger in logout_triggers):
            return ("logout", "")
        
        # Check for system status commands
        system_triggers = ["hoe draaien je systemen", "systeem status", "hoe gaat het met je", "alles ok", "draai je goed"]
        if any(trigger in text_lower for trigger in system_triggers):
            return ("system_status", "")
        
        # Check for "Spark zeg eens" command (admin only - gradatie 1)
        # Pattern: "Spark zeg eens: [tekst]" or "zeg eens: [tekst]"
        say_pattern = r"(?:spark\s+)?zeg\s+eens[:\s]+(.+)"
        say_match = re.search(say_pattern, text_lower, re.IGNORECASE)
        if say_match:
            message_to_say = say_match.group(1).strip()
            # Return original text (not lowercased) for the actual message
            original_match = re.search(say_pattern, text, re.IGNORECASE)
            if original_match:
                return ("say_command", original_match.group(1).strip())
        
        # Check for trigger lijst beheer commands (admin only)
        if text_lower in ["/triggers", "triggers", "trigger lijst", "trigger manager"]:
            return ("triggers_menu", "")
        
        # Check for trigger view commands
        if text_lower.startswith("/triggers view") or text_lower.startswith("triggers view"):
            parts = text_lower.split()
            if len(parts) >= 3:
                list_key = parts[2]  # a, b, c, d
                return ("triggers_view", list_key)
        
        # Check for trigger move commands
        if "triggers move" in text_lower or "/triggers move" in text_lower:
            # Format: /triggers move [woord] van [emotie1] naar [emotie2]
            return ("triggers_move", text)
        
        # Check for trigger remove commands
        if "triggers remove" in text_lower or "/triggers remove" in text_lower:
            # Format: /triggers remove [woord] van [emotie]
            return ("triggers_remove", text)
        
        # Check for achievement celebration (user telling us they unlocked one)
        # MUST be BEFORE general achievements check (more specific match)
        achievement_phrases = [
            "achievement gehaald", "achievement bereikt", "milestone gehaald", 
            "milestone bereikt", "level up", "ik heb een achievement",
            "achievement unlocked", "nieuwe achievement", "achievement gekregen",
            "ik haalde een achievement", "yes achievement", "achievement!",
            "ik heb zojuist een achievement"
        ]
        if any(phrase in text_lower for phrase in achievement_phrases):
            return ("achievement_celebration", "")
        
        # Check for achievements command (IMPROVED: natural language variations)
        achievement_view_triggers = [
            "/achievements", "achievements", "mijn achievements", "achievement",
            "voortgang", "mijn voortgang", "bekijk mijn achievements", 
            "laat mijn achievements zien", "laat achievements zien",
            "toon mijn achievements", "show achievements", "achievement status",
            "hoeveel achievements", "welke achievements"
        ]
        if any(trigger in text_lower for trigger in achievement_view_triggers):
            return ("achievements", "")
        
        # DON'T auto-detect single letters as trigger_select
        # That happens in spark_brain when there's context
        
        # Check for dagboek entry commands (met "Note dagboek:" prefix)
        dagboek_patterns = [
            r"note\s+dagboek[:\s]+(.+)",
            r"dagboek entry[:\s]+(.+)",
            r"dagboek[:\s]+(.+)",
            r"schrijf in dagboek[:\s]+(.+)",
        ]
        for pattern in dagboek_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                return ("dagboek_entry", content)
        
        # Check for agenda/afspraak commands (met "Note agenda:" prefix)
        agenda_patterns = [
            r"note\s+agenda[:\s]+(.+)",
            r"afspraak[:\s]+(.+)",
            r"agenda[:\s]+(.+)",
            r"voeg afspraak toe[:\s]+(.+)",
            r"plan[:\s]+(.+)",
        ]
        for pattern in agenda_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                return ("agenda_event", content)
        
        # Check for yes/no responses (for account creation flow)
        if text_lower in ["ja", "yes", "yep", "ok", "okay", "graag", "doe maar"]:
            return ("yes_response", "")
        
        if text_lower in ["nee", "no", "nope", "niet", "liever niet"]:
            return ("no_response", "")
        
        # Check for "Ja. [info]" pattern (user wants to teach)
        if text_lower.startswith("ja.") or text_lower.startswith("ja,"):
            # Extract what comes after "ja"
            content = text[3:].strip()
            if content and ("is" in content or "=" in content):
                return ("learn", content)
        
        # Check for learning commands
        leer_woorden = self.keywords.get("commando", {}).get("woorden", {}).get("leren", [])
        for word in leer_woorden:
            if word in text_lower:
                # Extract what to remember
                content = text.replace(word, "", 1).strip()
                if content:
                    return ("learn", content)
        
        # Check for forget commands
        vergeet_woorden = self.keywords.get("commando", {}).get("woorden", {}).get("vergeten", [])
        for word in vergeet_woorden:
            if word in text_lower:
                content = text.replace(word, "", 1).strip()
                if content:
                    return ("forget", content)
        
        # Check for show commands
        toon_woorden = self.keywords.get("commando", {}).get("woorden", {}).get("tonen", [])
        for word in toon_woorden:
            if word in text_lower:
                content = text.replace(word, "", 1).strip()
                if content:
                    return ("show", content)
        
        # Diary command
        if "dagboek" in text_lower:
            if any(w in text_lower for w in ["toon", "laat zien", "geef"]):
                return ("show_diary", "")
            elif any(w in text_lower for w in ["entry", "schrijf", "onthoud"]):
                # Extract diary content
                patterns = [
                    r"dagboek\s+entry[:\s]+(.+)",
                    r"dagboek[:\s]+(.+)"
                ]
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return ("diary_entry", match.group(1).strip())
        
        # Note command (for brainfarts and insights)
        if text_lower.startswith("note:") or text_lower.startswith("notitie:"):
            content = text.split(":", 1)[1].strip() if ":" in text else ""
            if content:
                return ("note", content)
        
        # Emotion command (admin)
        if text_lower.startswith("emotie:"):
            content = text.split(":", 1)[1].strip() if ":" in text else ""
            return ("emotion", content)
        
        return None
    
    def correct_typos(self, word: str, vocabulary: list, threshold: int = 2) -> Optional[str]:
        """
        Correct typos using Levenshtein distance
        """
        if not vocabulary:
            return None
        
        min_distance = float('inf')
        best_match = None
        
        for vocab_word in vocabulary:
            dist = levenshtein_distance(word.lower(), vocab_word.lower())
            if dist < min_distance and dist <= threshold:
                min_distance = dist
                best_match = vocab_word
        
        return best_match
    
    def is_greeting(self, text: str) -> bool:
        """Check if text is a greeting"""
        text_lower = text.lower()
        # Use conversation_triggers instead of hardcoded keywords
        greetings = self.conversation_triggers.get("greetings", {}).get("triggers", [])
        
        # Log trigger detection for verification
        if any(greeting in text_lower for greeting in greetings):
            print(f"[TRIGGER] Conversation: greeting detected - '{text[:30]}'")
            return True
        return False
    
    def detect_how_are_you(self, text: str) -> bool:
        """Check if text is a 'how are you' question (NEW)"""
        text_lower = text.lower()
        triggers = self.conversation_triggers.get("how_are_you", {}).get("triggers", [])
        
        if any(trigger in text_lower for trigger in triggers):
            print(f"[TRIGGER] Conversation: how_are_you detected - '{text[:30]}'")
            return True
        return False
    
    def detect_thanks(self, text: str) -> bool:
        """Check if text is a thank you message (NEW)"""
        text_lower = text.lower()
        triggers = self.conversation_triggers.get("thanks", {}).get("triggers", [])
        
        if any(trigger in text_lower for trigger in triggers):
            print(f"[TRIGGER] Conversation: thanks detected - '{text[:30]}'")
            return True
        return False
    
    def is_question(self, text: str) -> bool:
        """Check if text is a question"""
        text_lower = text.lower()
        vraag_woorden = self.keywords.get("vragen", {}).get("woorden", [])
        return any(word in text_lower for word in vraag_woorden) or text.strip().endswith('?')
