"""
Migratie script: Notes van globaal naar per-user
"""
import json
from pathlib import Path
from datetime import datetime

def migrate_notes_to_per_user():
    """Migreer globale notes.json naar per-user structuur"""
    
    # Lees globale notes
    global_notes_path = Path("/app/backend/data/notes/notes.json")
    
    if not global_notes_path.exists():
        print("❌ Geen globale notes.json gevonden")
        return
    
    with open(global_notes_path, 'r', encoding='utf-8') as f:
        global_data = json.load(f)
    
    notes = global_data.get("notes", [])
    
    if not notes:
        print("✅ Geen notes om te migreren")
        return
    
    print(f"📊 Gevonden: {len(notes)} notes in globaal bestand")
    
    # Groepeer notes per created_by (als user identifier)
    users_notes = {}
    for note in notes:
        creator = note.get("created_by", "Spark")
        if creator not in users_notes:
            users_notes[creator] = []
        users_notes[creator].append(note)
    
    print(f"👥 Notes verdeeld over {len(users_notes)} gebruikers:")
    for user, user_notes in users_notes.items():
        print(f"   - {user}: {len(user_notes)} notes")
    
    # Vraag om bevestiging
    print("\n⚠️  MIGRATIE PLAN:")
    print("   1. Globale notes blijven als backup")
    print("   2. Notes worden gekopieerd naar /users/{user_id}/notes.json")
    print("   3. Default user_id: 'admin' (voor Spark notes)")
    print()
    
    # Voor deze migratie: alle notes naar 'admin' user
    # (in productie zou je dit per echte user_id doen)
    target_user = "admin"
    
    # Maak user folder
    user_folder = Path(f"/app/backend/data/users/{target_user}")
    user_folder.mkdir(parents=True, exist_ok=True)
    
    # Maak user notes file
    user_notes_path = user_folder / "notes.json"
    user_data = {
        "user_id": target_user,
        "notes": notes,  # Alle notes
        "created_at": datetime.now().isoformat(),
        "migrated_from": "global_notes.json",
        "migration_date": datetime.now().isoformat()
    }
    
    with open(user_notes_path, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Gemigreerd: {len(notes)} notes naar /users/{target_user}/notes.json")
    print(f"📁 Backup: Origineel blijft op {global_notes_path}")
    print()
    print("🎉 Migratie compleet!")
    print()
    print("📝 VOLGENDE STAPPEN:")
    print("   1. Test de nieuwe API met user_id=admin")
    print("   2. Verifieer dat frontend nog werkt")
    print("   3. Optioneel: rename global notes naar notes.json.backup")

if __name__ == "__main__":
    migrate_notes_to_per_user()
