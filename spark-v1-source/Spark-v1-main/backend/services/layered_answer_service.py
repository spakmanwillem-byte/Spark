"""
Layered Answer Service - 4-Lagen Kennis Systeem (Appel Concept)

Laag 1: Kort antwoord (direct, simpel)
Laag 2: + Voorwoord (context, waarom belangrijk)
Laag 3: + Volledige omschrijving (diepgaand, complete info)
Laag 4: + Uitgebreide context / relaties / graph (associatief netwerk)
"""

from typing import Dict, Optional, List
from utils.data_manager import DataManager


class LayeredAnswerService:
    
    @staticmethod
    def get_layered_answer(begrip: str, requested_layer: int = 1) -> Optional[Dict]:
        """
        Get knowledge answer with specific layer depth
        
        Args:
            begrip: The concept/term to explain
            requested_layer: 1, 2, 3, or 4 (default: 1)
            
        Returns:
            Dict with answer and metadata (including knowledge_id for tracking)
        """
        # Load knowledge base
        knowledge = DataManager.load_knowledge()
        
        # Search for the concept (case-insensitive)
        begrip_lower = begrip.lower()
        found_entry = None
        
        for entry in knowledge:
            if entry.get("begrip", "").lower() == begrip_lower:
                found_entry = entry
                break
        
        if not found_entry:
            return None
        
        # Extract layers
        lagen = found_entry.get("lagen", {})
        
        # Build layered response
        response = {
            "begrip": found_entry.get("begrip"),
            "knowledge_id": found_entry.get("id"),  # ← IMPORTANT for tracking
            "layer": requested_layer,
            "available_layers": LayeredAnswerService._count_available_layers(lagen),
            "content": LayeredAnswerService._build_layer_content(lagen, requested_layer),
            "tags": found_entry.get("tags", []),
            "has_more": LayeredAnswerService._count_available_layers(lagen) > requested_layer
        }
        
        return response
    
    @staticmethod
    def _count_available_layers(lagen: Dict) -> int:
        """Count how many layers have content"""
        count = 0
        if lagen.get("laag1"):
            count += 1
        if lagen.get("laag2"):
            count += 1
        if lagen.get("laag3"):
            count += 1
        if lagen.get("laag4"):
            count += 1
        return count
    
    @staticmethod
    def _build_layer_content(lagen: Dict, requested_layer: int) -> str:
        """
        Build content string based on requested layer
        Each layer includes all previous layers
        """
        content = ""
        
        # Layer 1: Basis (always included)
        laag1 = lagen.get("laag1", "")
        if laag1:
            content = laag1
        
        # Layer 2: Add voorwoord/context
        if requested_layer >= 2:
            laag2 = lagen.get("laag2", "")
            if laag2:
                content += f"\n\n{laag2}"
        
        # Layer 3: Add full description
        if requested_layer >= 3:
            laag3 = lagen.get("laag3", "")
            if laag3:
                content += f"\n\n{laag3}"
        
        # Layer 4: Add graph/relaties/uitgebreide context
        if requested_layer >= 4:
            laag4 = lagen.get("laag4", "")
            if laag4:
                content += f"\n\n{laag4}"
        
        return content.strip()
    
    @staticmethod
    def format_layered_response(answer_data: Dict, show_layer_info: bool = False) -> str:
        """
        Format layered answer for chat display
        
        Args:
            show_layer_info: If True, show layer indicators (admin mode)
        """
        if not answer_data:
            return ""
        
        begrip = answer_data.get("begrip")
        layer = answer_data.get("layer")
        content = answer_data.get("content")
        has_more = answer_data.get("has_more", False)
        
        # Build response
        if show_layer_info:
            # Admin mode: show layer info
            layer_emoji = "🍎" if layer == 1 else "🍏" if layer == 2 else "🌳" if layer == 3 else "🌐"
            response = f"{layer_emoji} **{begrip}** (Laag {layer})\n\n{content}"
            
            # Add prompt for more info
            if has_more:
                response += f"\n\n💡 _Type 'meer' of 'dieper' voor meer details (laag {layer + 1})_"
        else:
            # Regular user: no layer indicators
            response = f"**{begrip}**\n\n{content}"
        
        return response
    
    @staticmethod
    def detect_layer_request(message: str) -> Optional[int]:
        """
        Detect if user wants a specific layer or deeper info
        
        Returns:
            Layer number (1, 2, 3) or None
        """
        message_lower = message.lower()
        
        # Check for explicit layer request
        if "laag 1" in message_lower or "kort" in message_lower:
            return 1
        elif "laag 2" in message_lower or "meer" in message_lower or "context" in message_lower:
            return 2
        elif "laag 3" in message_lower or "volledig" in message_lower or "diep" in message_lower or "compleet" in message_lower:
            return 3
        elif "laag 4" in message_lower or "graph" in message_lower or "relaties" in message_lower or "netwerk" in message_lower:
            return 4
        
        # Check for "deeper" request
        if any(word in message_lower for word in ["meer", "dieper", "verder", "uitleg", "leg uit"]):
            return 2  # Default to layer 2 for "more info"
        
        return None
