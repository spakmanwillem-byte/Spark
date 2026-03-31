"""
Spark Intent & Mode Manager
Simpele intent detection en mode switching voor Spark responses
"""

# In-memory context per user
USER_MODES = {}

# Intent patterns (expliciete triggers)
INTENT_PATTERNS = {
    "kort": ["kort", "beknopt", "kort graag", "snel", "tldr"],
    "uitleg": ["leg uit", "uitleg", "vertel meer", "uitgebreid", "explain"],
    "brainstorm": ["brainstorm", "ideeën", "brainstorm mee", "denk mee"],
    "help": ["help", "hulp", "commands", "wat kan je"]
}

def detect_mode_switch(message: str, user_id: str) -> dict:
    """
    Detect als user expliciet mode wil switchen of help vraagt
    Returns: {"switched": bool, "new_mode": str, "message": str}
    """
    message_lower = message.lower().strip()
    
    # Check for help command (special case - geen mode switch)
    for pattern in INTENT_PATTERNS.get("help", []):
        if pattern in message_lower:
            current_mode = USER_MODES.get(user_id, "normal")
            help_text = f"""🔧 **Beschikbare commands:**

• **kort** → Korte, beknopte antwoorden
• **uitleg** → Uitgebreide uitleg met context
• **brainstorm** → Ideeën genereren en structureren
• **help** → Dit overzicht tonen

Je bent nu in: **{current_mode}** mode"""
            
            return {
                "switched": True,
                "new_mode": current_mode,  # Mode blijft hetzelfde
                "message": help_text,
                "is_help": True
            }
    
    # Check for explicit mode switches
    for mode, patterns in INTENT_PATTERNS.items():
        if mode == "help":  # Skip help, already handled
            continue
            
        for pattern in patterns:
            if pattern in message_lower:
                old_mode = USER_MODES.get(user_id, "normal")
                USER_MODES[user_id] = mode
                
                return {
                    "switched": True,
                    "old_mode": old_mode,
                    "new_mode": mode,
                    "message": f"✅ Mode switched naar: {mode}"
                }
    
    # No switch detected
    return {
        "switched": False,
        "current_mode": USER_MODES.get(user_id, "normal")
    }

def get_user_mode(user_id: str) -> str:
    """Get current mode for user"""
    return USER_MODES.get(user_id, "normal")

def set_user_mode(user_id: str, mode: str):
    """Manually set mode for user"""
    if mode in ["kort", "uitleg", "brainstorm", "normal"]:
        USER_MODES[user_id] = mode
        return True
    return False

def format_response(content: str, user_id: str) -> str:
    """
    Format response based on user's current mode
    """
    mode = get_user_mode(user_id)
    
    if mode == "kort":
        # Beknopt: eerste 2 zinnen of 150 chars
        sentences = content.split('. ')
        if len(sentences) > 2:
            return '. '.join(sentences[:2]) + '.'
        elif len(content) > 150:
            return content[:150] + '...'
        return content
    
    elif mode == "uitleg":
        # Uitgebreid: add context/examples
        # Voor nu: gewoon volledig + tip
        return content + "\n\n💡 Tip: Vraag 'kort' voor beknopte antwoorden."
    
    elif mode == "brainstorm":
        # Brainstorm: structureer als ideeën
        if "idee" not in content.lower() and "optie" not in content.lower():
            # Wrap in brainstorm format
            return f"💭 **Brainstorm:**\n\n{content}\n\n🎯 Andere ideeën? Laat het me weten!"
        return content
    
    else:
        # Normal mode: geen aanpassingen
        return content

# Example usage
if __name__ == "__main__":
    # Test mode switching
    user = "user-001"
    
    print("Test 1: Kort mode")
    result = detect_mode_switch("kort graag", user)
    print(result)
    
    print("\nTest 2: Format in kort mode")
    long_text = "Dit is een lange tekst met veel informatie. Zin twee heeft ook veel details. Zin drie is ook belangrijk. En nog meer."
    formatted = format_response(long_text, user)
    print(formatted)
    
    print("\nTest 3: Brainstorm mode")
    detect_mode_switch("brainstorm mee", user)
    formatted = format_response("We kunnen A doen, of misschien B, of zelfs C.", user)
    print(formatted)
    
    print(f"\nCurrent mode: {get_user_mode(user)}")
