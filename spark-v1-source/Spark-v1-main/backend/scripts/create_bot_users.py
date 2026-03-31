#!/usr/bin/env python3
"""
Create bot users in Spark system
"""
import json
from pathlib import Path

USERS_FILE = Path("/app/backend/data/system/users.json")

# Bot users to add
bots = [
    {
        "id": "bot-madelief",
        "naam": "Madelief Stouten",
        "volledige_naam": "Madelief Stouten",
        "email": "madelief@spark.bot",
        "type": "bot",
        "sleutelwoord": "Stouten",
        "gradatie": 3,
        "xp": 150,
        "credits": 0,
        "rank": "Bot Assistant",
        "persoonlijke_info": {
            "bio": "Ik ben Madelief! Ik hou iedereen gezelschap en zorg dat niemand zich alleen voelt. 👋",
            "persoonlijkheid": "Sociaal, vriendelijk, enthousiast",
            "rol": "Community Greeter & Social Bot"
        }
    },
    {
        "id": "bot-harry",
        "naam": "Harry Klokkenmaker",
        "volledige_naam": "Harry Klokkenmaker",
        "email": "harry@spark.bot",
        "type": "bot",
        "sleutelwoord": "Klokkenmaker",
        "gradatie": 3,
        "xp": 200,
        "credits": 0,
        "rank": "Bot Assistant",
        "persoonlijke_info": {
            "bio": "Ik ben Harry. De tijd is mijn specialiteit. Vraag me hoe laat het is! ⏰",
            "persoonlijkheid": "Punctueel, precies, betrouwbaar",
            "rol": "Time Keeper & Scheduler Bot"
        }
    },
    {
        "id": "bot-smith",
        "naam": "Mr Smith",
        "volledige_naam": "Mr Smith",
        "email": "smith@spark.bot",
        "type": "bot",
        "sleutelwoord": "Smith",
        "gradatie": 5,
        "xp": 500,
        "credits": 0,
        "rank": "Bot Security",
        "persoonlijke_info": {
            "bio": "Ik ben Mr Smith. Ik houd het systeem veilig en scan op problemen. 🕵️",
            "persoonlijkheid": "Analytisch, observerend, security-minded",
            "rol": "Security Scanner & System Monitor"
        }
    }
]

def add_bots_to_users():
    """Add bot users to system"""
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
    
    users = data.get('users', [])
    
    # Check if bots already exist
    existing_bot_ids = [u['id'] for u in users if u.get('type') == 'bot']
    
    added_count = 0
    for bot in bots:
        if bot['id'] not in existing_bot_ids:
            users.append(bot)
            added_count += 1
            print(f"✅ Added: {bot['naam']} (sleutelwoord: {bot['sleutelwoord']})")
        else:
            print(f"⏭️  Skipped: {bot['naam']} (already exists)")
    
    # Save
    data['users'] = users
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Added {added_count} bot users to system!")
    print(f"   Total users now: {len(users)}")
    
    # Add to leaderboard with fake scores
    print("\n🏆 Bots op Leaderboard:")
    for bot in bots:
        print(f"   {bot['naam']}: {bot['xp']} XP, Rank: {bot['rank']}")

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 CREATING BOT USERS")
    print("=" * 60)
    add_bots_to_users()
    print("=" * 60)
