"""
Context Engine - Combineert user profiles, notities en patronen voor slimme antwoorden
"""
from typing import Dict, List, Optional
from services.user_profile_service import UserProfileService
from services.notes_service import NotesService
from services.pattern_detection_service import PatternDetectionService


class ContextEngine:
    """Engine die context combineert voor intelligente responses"""
    
    @staticmethod
    def get_user_context(user_id: str, current_message: str = "") -> Dict:
        """
        Haal alle relevante context op voor een user
        
        Returns:
            {
                "profile": Dict,  # need, believe, interesses, etc.
                "relevant_notes": List[Dict],  # Relevante notities
                "patterns": Dict,  # Gedetecteerde patronen
                "context_summary": str  # Tekstuele samenvatting voor AI
            }
        """
        # Haal user profile op
        user = UserProfileService.get_user_profile(user_id)
        profile = user.get("profile", {}) if user else {}
        
        # Haal relevante notities op (van deze user)
        all_notes = NotesService.get_all_notes(user_id)
        relevant_notes = ContextEngine._find_relevant_notes(current_message, all_notes)
        
        # Analyse current message voor patronen
        current_analysis = PatternDetectionService.analyze_message(current_message, user)
        
        # Maak context summary
        context_summary = ContextEngine._build_context_summary(
            user_name=user.get("naam", "User") if user else "User",
            profile=profile,
            relevant_notes=relevant_notes,
            current_analysis=current_analysis
        )
        
        return {
            "profile": profile,
            "relevant_notes": relevant_notes,
            "patterns": current_analysis,
            "context_summary": context_summary,
            "user_name": user.get("naam") if user else None
        }
    
    @staticmethod
    def _find_relevant_notes(message: str, all_notes: List[Dict], limit: int = 3) -> List[Dict]:
        """Vind notities die relevant zijn voor het huidige bericht"""
        if not message or not all_notes:
            return []
        
        message_lower = message.lower()
        message_words = set(message_lower.split())
        
        # Score notes based on relevance
        scored_notes = []
        
        for note in all_notes:
            score = 0
            note_text = (note.get("titel", "") + " " + note.get("inhoud", "")).lower()
            note_words = set(note_text.split())
            
            # Overlap in woorden
            overlap = len(message_words & note_words)
            score += overlap * 2
            
            # Categorie bonus
            if note.get("categorie") in ["Inzicht", "Patroon"]:
                score += 5
            
            # Tags match
            tags = note.get("tags", [])
            for tag in tags:
                if tag.lower() in message_lower:
                    score += 3
            
            if score > 0:
                scored_notes.append((score, note))
        
        # Sort en return top N
        scored_notes.sort(key=lambda x: x[0], reverse=True)
        return [note for score, note in scored_notes[:limit]]
    
    @staticmethod
    def _build_context_summary(user_name: str, profile: Dict, relevant_notes: List[Dict], current_analysis: Dict) -> str:
        """Bouw een tekstuele samenvatting van de context"""
        summary_parts = []
        
        # User profile context
        if profile.get("need") or profile.get("believe"):
            summary_parts.append("📋 User Context:")
            if profile.get("need"):
                summary_parts.append(f"  - Need: {profile['need']}")
            if profile.get("believe"):
                summary_parts.append(f"  - Believe: {profile['believe']}")
            if profile.get("interesses"):
                summary_parts.append(f"  - Interesses: {', '.join(profile['interesses'][:3])}")
        
        # Relevant notes
        if relevant_notes:
            summary_parts.append("\n💡 Relevante Notities:")
            for note in relevant_notes[:2]:
                summary_parts.append(f"  - {note.get('titel', 'Notitie')}: {note.get('inhoud', '')[:100]}...")
        
        # Current patterns
        if current_analysis.get("has_stop_words"):
            summary_parts.append(f"\n⚠️ Belangrijk: User gebruikt stopwoorden: {', '.join(current_analysis['stop_words_found'])}")
        
        if current_analysis.get("emotional_tone") != "neutraal":
            summary_parts.append(f"😊 Emotionele toon: {current_analysis['emotional_tone']}")
        
        if current_analysis.get("topics"):
            summary_parts.append(f"🎯 Onderwerpen: {', '.join(current_analysis['topics'][:3])}")
        
        return "\n".join(summary_parts) if summary_parts else "Geen specifieke context beschikbaar."
    
    @staticmethod
    def should_create_note(context: Dict) -> bool:
        """Bepaal of er automatisch een notitie aangemaakt moet worden"""
        patterns = context.get("patterns", {})
        return patterns.get("should_remember", False)
    
    @staticmethod
    def enhance_response(base_response: str, context: Dict) -> str:
        """
        Verbeter een response met context-awareness
        
        Voegt personalisatie toe gebaseerd op profile en patterns
        """
        profile = context.get("profile", {})
        patterns = context.get("patterns", {})
        user_name = context.get("user_name", "")
        
        enhanced = base_response
        
        # Als user belangrijk woorden gebruikt, erken dit
        if patterns.get("has_stop_words") and patterns.get("importance_score", 0) >= 4:
            enhanced = f"Ik hoor dat dit belangrijk voor je is. {enhanced}"
        
        # Als er emotionele toon is, reageer erop
        emotional_tone = patterns.get("emotional_tone")
        if emotional_tone == "negatief":
            enhanced = f"Ik merk dat je misschien zorgen hebt. {enhanced}"
        elif emotional_tone == "positief":
            enhanced = f"Wat fijn om te horen! {enhanced}"
        
        # Suggestie om te onthouden
        if patterns.get("should_remember"):
            enhanced += "\n\n💡 _Dit lijkt belangrijk. Zal ik dit onthouden in mijn notities?_"
        
        return enhanced
    
    @staticmethod
    def get_personalized_greeting(user_id: str) -> str:
        """Maak een gepersonaliseerde begroeting"""
        user = UserProfileService.get_user_profile(user_id)
        
        if not user:
            return "Hey! Wat kan ik voor je doen?"
        
        profile = user.get("profile", {})
        name = user.get("naam", "")
        
        greeting = f"Hey {name}! "
        
        # Personaliseer op basis van profile
        if profile.get("need"):
            need = profile["need"].lower()
            if "impact" in need or "helpen" in need:
                greeting += "Klaar om samen impact te maken? "
            elif "begrip" in need or "erkenning" in need:
                greeting += "Ik ben er voor je. "
        
        greeting += "Wat kan ik voor je doen?"
        
        return greeting
