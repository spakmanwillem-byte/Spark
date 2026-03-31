"""
Cleanup Script - Verwijder Test Users
Houdt alleen Willem, Lotus, Maurice
"""
import json
from pathlib import Path

users_file = Path("/app/backend/data/system/users.json")

# Load
with open(users_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

users = data.get('users', [])
print(f'📊 Total users VOOR cleanup: {len(users)}')

# Keep only real users
real_user_ids = ['user-001', 'user-lotus', 'user-maurice']
cleaned_users = [u for u in users if u.get('id') in real_user_ids]

print(f'\n✅ Keeping {len(cleaned_users)} real users:')
for u in cleaned_users:
    print(f'  - {u.get("naam")} ({u.get("id")})')

print(f'\n❌ Removing {len(users) - len(cleaned_users)} test users')

# Update
data['users'] = cleaned_users
data['metadata']['last_cleanup'] = '2026-03-15T00:00:00Z'
data['metadata']['cleaned_count'] = len(users) - len(cleaned_users)

# Save
with open(users_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'\n💾 Saved! Total users NA cleanup: {len(cleaned_users)}')
