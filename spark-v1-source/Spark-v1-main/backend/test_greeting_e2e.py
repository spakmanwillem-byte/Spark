"""
Test Greeting Triggers - End to End
====================================
Test via /api/spark/chat endpoint
"""

import requests
import json

API = "http://localhost:8001/api/spark/chat"

test_messages = [
    "Hallo Spark",
    "Hey Spark hoe gaat het?",
    "Goedemorgen Spark",
    "Hi Spark!",
    "Goedemiddag Spark",
    "Avond Spark",
    "Wat is Bitcoin?",  # Geen trigger - normale flow
]

print("=" * 60)
print("🧪 END-TO-END GREETING TEST")
print("=" * 60)

for msg in test_messages:
    print(f"\n📝 USER: {msg}")
    
    try:
        response = requests.post(
            API,
            json={
                "message": msg,
                "user_id": None,
                "session_id": "test_session"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            spark_response = data.get('response', '')
            
            # Check of het een greeting response is (kort, geen definitie)
            is_greeting = len(spark_response) < 100 and not spark_response.startswith('"')
            
            if is_greeting:
                print(f"   ✅ SPARK (trigger): {spark_response}")
            else:
                print(f"   💬 SPARK (normal): {spark_response[:100]}...")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

print("\n" + "=" * 60)
print("✅ Test complete!")
print("=" * 60)
