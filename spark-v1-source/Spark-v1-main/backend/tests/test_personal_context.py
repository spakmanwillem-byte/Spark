"""
Test Personal Context Service - Fase 1 MVP
Tests entity extraction, deduplication, and API
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_analyze_conversation():
    """Test 1: Analyze conversation and extract entities"""
    print("\n" + "="*60)
    print("TEST 1: Analyze Conversation")
    print("="*60)
    
    # Test input: Gesprek met moeder en zusje
    payload = {
        "user_id": "test_user_001",
        "text": "Mijn moeder belde gisteren, ze was boos omdat ik mijn zusje niet heb teruggebeld"
    }
    
    response = requests.post(f"{BASE_URL}/api/context/analyze", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['success']}")
        print(f"✅ Extracted entities: {len(data['extracted_entities'])}")
        for entity in data['extracted_entities']:
            print(f"   - {entity['role']} ({entity['relation']})")
        
        print(f"\n✅ Total entities in profile: {len(data['updated_profile']['entities'])}")
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_get_entities(user_id: str):
    """Test 2: Get all entities for user"""
    print("\n" + "="*60)
    print("TEST 2: Get User Entities")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/context/entities/{user_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User: {data['user_id']}")
        print(f"✅ Entities: {len(data['entities'])}")
        for entity in data['entities']:
            print(f"   - {entity['role']} ({entity['relation']}) - mentioned {entity['mention_count']}x")
            print(f"     Aliases: {entity.get('aliases', [])}")
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_get_entity_by_role(user_id: str, role: str):
    """Test 3: Get specific entity by role"""
    print("\n" + "="*60)
    print(f"TEST 3: Get Entity by Role ({role})")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/context/entity/{user_id}/{role}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        entity = data['entity']
        print(f"✅ Found: {entity['role']} ({entity['relation']})")
        print(f"   Aliases: {entity.get('aliases', [])}")
        print(f"   Mentioned: {entity['mention_count']}x")
        return data
    else:
        print(f"❌ Error: {response.text}")
        return None

def test_deduplication():
    """Test 4: Test deduplication with aliases"""
    print("\n" + "="*60)
    print("TEST 4: Deduplication (Aliases)")
    print("="*60)
    
    # First mention: "moeder"
    payload1 = {
        "user_id": "test_user_002",
        "text": "Mijn moeder belde gisteren"
    }
    
    response1 = requests.post(f"{BASE_URL}/api/context/analyze", json=payload1)
    data1 = response1.json()
    print(f"✅ First mention: {len(data1['updated_profile']['entities'])} entity")
    
    # Second mention: "ma" (should merge with "moeder")
    payload2 = {
        "user_id": "test_user_002",
        "text": "Ma snapt het gewoon niet"
    }
    
    response2 = requests.post(f"{BASE_URL}/api/context/analyze", json=payload2)
    data2 = response2.json()
    print(f"✅ Second mention: {len(data2['updated_profile']['entities'])} entity (should still be 1)")
    
    # Check if merged
    entity = data2['updated_profile']['entities'][0]
    print(f"✅ Entity role: {entity['role']}")
    print(f"✅ Aliases: {entity.get('aliases', [])}")
    print(f"✅ Mention count: {entity['mention_count']}")
    
    if entity['mention_count'] == 2 and 'ma' in entity['aliases']:
        print("\n✅ DEDUPLICATION WORKS!")
    else:
        print("\n❌ DEDUPLICATION FAILED")
    
    return data2

def test_multiple_relations():
    """Test 5: Multiple entities with different relations"""
    print("\n" + "="*60)
    print("TEST 5: Multiple Relations")
    print("="*60)
    
    payload = {
        "user_id": "test_user_003",
        "text": "Mijn vader, moeder, broer en zusje gingen op vakantie"
    }
    
    response = requests.post(f"{BASE_URL}/api/context/analyze", json=payload)
    data = response.json()
    
    print(f"✅ Extracted: {len(data['extracted_entities'])} entities")
    print(f"✅ Total in profile: {len(data['updated_profile']['entities'])} entities")
    
    for entity in data['updated_profile']['entities']:
        print(f"   - {entity['role']} ({entity['relation']})")
    
    return data

def test_clear_context(user_id: str):
    """Test 6: Clear user context"""
    print("\n" + "="*60)
    print("TEST 6: Clear Context")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/api/context/clear/{user_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        
        # Verify cleared
        verify = requests.get(f"{BASE_URL}/api/context/entities/{user_id}")
        verify_data = verify.json()
        print(f"✅ Entities after clear: {len(verify_data['entities'])}")
        return True
    else:
        print(f"❌ Error: {response.text}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PERSONAL CONTEXT SERVICE - TEST SUITE")
    print("="*60)
    
    # Run all tests
    test_analyze_conversation()
    test_get_entities("test_user_001")
    test_get_entity_by_role("test_user_001", "moeder")
    test_deduplication()
    test_multiple_relations()
    test_clear_context("test_user_001")
    test_clear_context("test_user_002")
    test_clear_context("test_user_003")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60)
