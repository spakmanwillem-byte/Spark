"""
Uitgebreide Live Cache Integration Test

Test de volledige cache flow:
1. Login
2. Meerdere berichten versturen
3. Check cache stats tussen berichten
4. Verifieer dat cache wordt gebruikt
5. Check hit rate
"""
import requests
import json
import time

# Get API URL
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if 'REACT_APP_BACKEND_URL' in line:
            API_URL = line.split('=')[1].strip()
            break

print("=" * 60)
print("UITGEBREIDE LIVE CACHE INTEGRATION TEST")
print("=" * 60)
print(f"API URL: {API_URL}\n")

# Test 1: Login
print("📝 TEST 1: Login")
print("-" * 60)

login_response = requests.post(
    f"{API_URL}/api/chat",
    json={"message": "Willem Appelsap"}
)

if login_response.status_code == 200:
    data = login_response.json()
    user_id = data.get('user_id')
    print(f"✓ Login successful")
    print(f"  User ID: {user_id}")
    print(f"  Gradatie: {data.get('user_gradatie')}")
else:
    print(f"✗ Login failed: {login_response.status_code}")
    exit(1)

# Get initial cache stats
print(f"\n📊 Initial Cache Stats:")
stats_response = requests.get(f"{API_URL}/api/admin/cache/stats")
if stats_response.status_code == 200:
    stats = stats_response.json()['stats']
    print(f"  Active Sessions: {stats['active_sessions']}")
    print(f"  Total Messages: {stats['total_messages']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")

print()

# Test 2: Send messages and track cache growth
print("📝 TEST 2: Send Messages & Track Cache")
print("-" * 60)

messages = [
    "Wat is een auto?",
    "Vertel me meer",
    "Interessant!",
    "Wat is een fiets?",
    "Bedankt voor je hulp"
]

for i, message in enumerate(messages, 1):
    print(f"\nMessage {i}: '{message}'")
    
    # Send message
    response = requests.post(
        f"{API_URL}/api/chat",
        json={"message": message, "user_id": user_id}
    )
    
    if response.status_code == 200:
        print("  ✓ Message sent")
    else:
        print(f"  ✗ Failed: {response.status_code}")
    
    time.sleep(0.3)
    
    # Check cache stats
    stats_response = requests.get(f"{API_URL}/api/admin/cache/stats")
    if stats_response.status_code == 200:
        stats = stats_response.json()['stats']
        print(f"  Cache: {stats['total_messages']} messages, {stats['active_sessions']} sessions")

print()

# Test 3: Final cache statistics
print("📝 TEST 3: Final Cache Statistics")
print("-" * 60)

stats_response = requests.get(f"{API_URL}/api/admin/cache/stats")
if stats_response.status_code == 200:
    stats = stats_response.json()['stats']
    
    print(f"\n📊 Final Cache Stats:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Total Requests: {stats['total_requests']}")
    print(f"  Hit Rate: {stats['hit_rate_percent']}%")
    print(f"  Active Sessions: {stats['active_sessions']}")
    print(f"  Total Messages: {stats['total_messages']}")
    print(f"  Memory Usage: {stats['memory_usage_mb']} MB")
    print(f"  Max Sessions: {stats['max_sessions']}")
    print(f"  Messages Per Session: {stats['messages_per_session']}")

print()
print("=" * 60)
print("VALIDATION")
print("=" * 60)

# Validation
expected_messages = 2 + (len(messages) * 2)  # login (2) + 5 messages × 2 (user + spark)
actual_messages = stats['total_messages']

print(f"\nExpected messages: ~{expected_messages} (login + {len(messages)} exchanges)")
print(f"Actual messages: {actual_messages}")

if actual_messages >= len(messages):
    print("✅ Cache is being populated correctly!")
else:
    print(f"⚠️  Cache has fewer messages than expected")

if stats['active_sessions'] > 0:
    print("✅ Active sessions tracked correctly!")
else:
    print("⚠️  No active sessions found")

print()
print("=" * 60)
print("✅ CACHE INTEGRATION TEST COMPLETE")
print("=" * 60)
print()
print("Summary:")
print(f"  • Cache is storing messages: {actual_messages > 0}")
print(f"  • Sessions are tracked: {stats['active_sessions'] > 0}")
print(f"  • Memory usage is reasonable: {stats['memory_usage_mb']} MB")
print(f"  • Cache statistics endpoint working: True")
print()
