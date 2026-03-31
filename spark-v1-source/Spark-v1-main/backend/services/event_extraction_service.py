"""
Event Extraction Service (JSON-driven)
Detects events from conversations using configurable triggers:
- Social events (helping family, visiting, meeting)
- Household tasks (gardening, cleaning, shopping)
- Work appointments
- Personal care (doctor, dentist)
- Leisure activities

Strategy: Load triggers from JSON for flexibility
"""
import re
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from utils.data_manager import DataManager


@dataclass
class DetectedEvent:
    """Simple event structure"""
    type: str  # "social", "household", "shopping", "work", "personal_care", "leisure", "other"
    title: str
    date_str: str  # Human readable: "zondag", "15 maart", "morgen"
    parsed_date: Optional[str]  # ISO format if parseable
    confidence: float
    original_text: str
    notes: str = ""


class EventExtractionService:
    """Extract events from natural language (JSON-driven)"""
    
    _triggers = None
    
    @staticmethod
    def _get_triggers() -> Dict:
        """Load triggers from JSON (cached)"""
        if EventExtractionService._triggers is None:
            EventExtractionService._triggers = DataManager.load_json("triggers/calendar_triggers.json")
        return EventExtractionService._triggers
    
    @staticmethod
    def extract_events(text: str) -> List[DetectedEvent]:
        """
        Extract events from text using JSON triggers
        Returns list of detected events
        """
        events = []
        text_lower = text.lower()
        triggers = EventExtractionService._get_triggers()
        event_categories = triggers.get("event_categories", {})
        
        # Check each category
        detected_category = None
        detected_keywords = []
        best_match_length = 0
        
        for category, category_data in event_categories.items():
            keywords = category_data.get("keywords", [])
            activities = category_data.get("activities", [])
            implicit_patterns = category_data.get("implicit_patterns", [])
            context_words = category_data.get("context", [])
            
            all_triggers = keywords + activities
            
            # Check explicit triggers first (prefer longer/more specific matches)
            for trigger in all_triggers:
                # Use word boundary matching for better accuracy
                import re
                pattern = r'\b' + re.escape(trigger) + r'\b'
                if re.search(pattern, text_lower):
                    # Prefer longer matches (more specific)
                    if len(trigger) > best_match_length:
                        detected_category = category
                        detected_keywords = [trigger]
                        best_match_length = len(trigger)
                    elif len(trigger) == best_match_length:
                        # Same length - add to keywords
                        if trigger not in detected_keywords:
                            detected_keywords.append(trigger)
            
            # Check implicit patterns (only if no explicit match yet)
            if not detected_category and implicit_patterns:
                for pattern in implicit_patterns:
                    if pattern in text_lower:
                        # Check if there's also a context word (family member, friend, etc.)
                        has_context = any(ctx in text_lower for ctx in context_words)
                        if has_context:
                            detected_category = category
                            detected_keywords = [pattern]
                            # Also add the context word
                            for ctx in context_words:
                                if ctx in text_lower:
                                    detected_keywords.append(ctx)
                                    break
                            break
        
        if detected_category:
            # Log trigger detection
            print(f"[TRIGGER] Calendar: {detected_category} detected - keywords: {detected_keywords} - '{text[:50]}'")
            
            # Extract event details
            event = EventExtractionService._extract_event(
                text=text,
                category=detected_category,
                keywords=detected_keywords
            )
            if event:
                events.append(event)
        
        return events
    
    @staticmethod
    def _extract_event(text: str, category: str, keywords: List[str]) -> Optional[DetectedEvent]:
        """
        Extract event details from text based on detected category
        """
        text_lower = text.lower()
        
        # Parse date
        date_str, parsed_date = EventExtractionService._parse_date(text)
        
        # Extract time if present
        time_match = re.search(r"(\d{1,2}):(\d{2})|(\d{1,2}) uur", text_lower)
        time_str = ""
        if time_match:
            if time_match.group(1):
                time_str = f" om {time_match.group(1)}:{time_match.group(2)}"
            else:
                time_str = f" om {time_match.group(3)}:00"
        
        # Create title based on category and keywords
        title = EventExtractionService._generate_title(text, category, keywords)
        
        # Determine confidence based on clarity
        confidence = 0.8 if (date_str or time_str) else 0.6
        
        return DetectedEvent(
            type=category,
            title=title,
            date_str=f"{date_str or 'binnenkort'}{time_str}",
            parsed_date=parsed_date,
            confidence=confidence,
            original_text=text,
            notes=f"Category: {category}, Keywords: {', '.join(keywords)}"
        )
    
    @staticmethod
    def _generate_title(text: str, category: str, keywords: List[str]) -> str:
        """Generate a meaningful title for the event"""
        text_lower = text.lower()
        
        # Category-based title generation
        if category == "social":
            # Extract person if mentioned
            person_indicators = ["moeder", "vader", "vriend", "vriendin", "oma", "opa", "familie"]
            for indicator in person_indicators:
                if indicator in text_lower:
                    return f"{keywords[0].capitalize()} {indicator}"
            return f"{keywords[0].capitalize()}"
        
        elif category == "household":
            # Include activity context
            if len(keywords) > 1:
                return f"{keywords[0].capitalize()} {keywords[1]}"
            return f"{keywords[0].capitalize()}"
        
        elif category == "shopping":
            return "Boodschappen doen"
        
        elif category == "work":
            return keywords[0].capitalize()
        
        elif category == "personal_care":
            return keywords[0].capitalize()
        
        elif category == "leisure":
            return keywords[0].capitalize()
        
        else:
            # Generic title from first keyword
            return keywords[0].capitalize() if keywords else "Gebeurtenis"
    
    # Dutch days of week (kept for date parsing)
    DAYS_OF_WEEK = {
        "maandag": 0, "dinsdag": 1, "woensdag": 2, "donderdag": 3,
        "vrijdag": 4, "zaterdag": 5, "zondag": 6,
        "ma": 0, "di": 1, "wo": 2, "do": 3, "vr": 4, "za": 5, "zo": 6
    }
    
    @staticmethod
    def _parse_date(text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Parse date from text (simple Dutch date parsing)
        Returns: (human_readable, iso_format)
        """
        text_lower = text.lower()
        today = datetime.now()
        
        # Relative dates
        if "morgen" in text_lower:
            date_obj = today + timedelta(days=1)
            return ("morgen", date_obj.date().isoformat())
        
        if "overmorgen" in text_lower:
            date_obj = today + timedelta(days=2)
            return ("overmorgen", date_obj.date().isoformat())
        
        if "vandaag" in text_lower:
            return ("vandaag", today.date().isoformat())
        
        # Days of week (assume next occurrence)
        for day_name, day_num in EventExtractionService.DAYS_OF_WEEK.items():
            if day_name in text_lower:
                # Calculate days until next occurrence
                current_day = today.weekday()
                days_ahead = (day_num - current_day) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week
                date_obj = today + timedelta(days=days_ahead)
                return (day_name, date_obj.date().isoformat())
        
        # Specific dates: "15 maart", "3 april"
        month_names = {
            "januari": 1, "februari": 2, "maart": 3, "april": 4,
            "mei": 5, "juni": 6, "juli": 7, "augustus": 8,
            "september": 9, "oktober": 10, "november": 11, "december": 12
        }
        
        for month_name, month_num in month_names.items():
            if month_name in text_lower:
                # Try to find day number
                day_match = re.search(r"(\d{1,2})\s+" + month_name, text_lower)
                if day_match:
                    day = int(day_match.group(1))
                    year = today.year
                    # If date has passed this year, assume next year
                    try:
                        date_obj = datetime(year, month_num, day)
                        if date_obj.date() < today.date():
                            date_obj = datetime(year + 1, month_num, day)
                        return (f"{day} {month_name}", date_obj.date().isoformat())
                    except ValueError:
                        pass
        
        return (None, None)
