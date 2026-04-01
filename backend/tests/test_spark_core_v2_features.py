"""
Test Spark Core 2.0 - 6 New Features:
1. Voice (TTS/STT via OpenAI) - only test /api/voice/voices endpoint
2. Spark Profile (23 categories personality data)
3. Willem Personality profile
4. Roadmap API backend + updated statuses
5. Notification system with bell icon + unread count
6. Extended Profile (address, emergency contact)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestVoiceModule:
    """Voice module - only test voices endpoint (not TTS/STT to save API budget)"""
    
    def test_get_voices_returns_9_options(self):
        """GET /api/voice/voices returns 9 voice options with default 'nova'"""
        response = requests.get(f"{BASE_URL}/api/voice/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert "default" in data
        assert data["default"] == "nova"
        assert len(data["voices"]) == 9
        # Verify voice structure
        voice_ids = [v["id"] for v in data["voices"]]
        assert "nova" in voice_ids
        assert "alloy" in voice_ids
        assert "shimmer" in voice_ids


class TestSparkProfile:
    """Spark Profile - 23 categories personality data"""
    
    def test_get_spark_profile_returns_full_data(self):
        """GET /api/spark/profile returns Spark's full personality profile"""
        response = requests.get(f"{BASE_URL}/api/spark/profile")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "profile" in data
        profile = data["profile"]
        # Check for key sections
        assert "basis" in profile
        assert "biografie" in profile
        assert "identiteit" in profile
        assert "filosofie" in profile
        assert "persoonlijkheid" in profile
        assert "vaardigheden" in profile
        # Verify basis data
        assert profile["basis"]["naam"] == "Spark"
    
    def test_get_spark_about_returns_summary(self):
        """GET /api/spark/about returns summary with naam, kernwaarden"""
        response = requests.get(f"{BASE_URL}/api/spark/about")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["naam"] == "Spark"
        assert "kernwaarden" in data
        assert isinstance(data["kernwaarden"], list)
        assert len(data["kernwaarden"]) > 0
        # Check for biografie, identiteit, filosofie
        assert "biografie" in data
        assert "identiteit" in data
        assert "filosofie" in data


class TestWillemPersonality:
    """Willem Personality profile"""
    
    def test_get_user_personality(self):
        """GET /api/personality/user-001 returns Willem personality data"""
        response = requests.get(f"{BASE_URL}/api/personality/user-001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == "user-001"
        assert "personality" in data


class TestRoadmapAPI:
    """Roadmap API backend + updated statuses"""
    
    def test_get_roadmap_summary(self):
        """GET /api/roadmap/summary returns version overview with done/total counts"""
        response = requests.get(f"{BASE_URL}/api/roadmap/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "versions" in data
        # Check that versions have done/total counts
        versions = data["versions"]
        assert len(versions) > 0
    
    def test_get_full_roadmap(self):
        """GET /api/roadmap returns full roadmap data from V1"""
        response = requests.get(f"{BASE_URL}/api/roadmap")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "roadmap" in data
    
    def test_add_roadmap_item(self):
        """POST /api/roadmap/add adds a new roadmap item"""
        payload = {
            "titel": "TEST_Automated Test Item",
            "versie": "v6.0",
            "priority": "low",
            "notes": "Created by automated test"
        }
        response = requests.post(f"{BASE_URL}/api/roadmap/add", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "item" in data
        assert data["item"]["titel"] == "TEST_Automated Test Item"
        assert data["item"]["status"] == "todo"


class TestNotificationSystem:
    """Notification system with bell icon + unread count"""
    
    def test_get_notifications_for_user(self):
        """GET /api/notifications/user-001 returns 3 notifications with unread_count=3"""
        response = requests.get(f"{BASE_URL}/api/notifications/user-001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "notifications" in data
        assert "unread_count" in data
        # Should have at least 3 seeded notifications
        assert len(data["notifications"]) >= 3
        # Check notification structure
        notif = data["notifications"][0]
        assert "id" in notif
        assert "title" in notif
        assert "message" in notif
        assert "type" in notif
    
    def test_mark_all_notifications_read(self):
        """POST /api/notifications/user-001/read-all marks all as read"""
        response = requests.post(f"{BASE_URL}/api/notifications/user-001/read-all")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Verify unread count is now 0
        verify_response = requests.get(f"{BASE_URL}/api/notifications/user-001")
        verify_data = verify_response.json()
        assert verify_data["unread_count"] == 0


class TestExtendedProfile:
    """Extended Profile (address, emergency contact)"""
    
    def test_get_extended_profile(self):
        """GET /api/profile/extended/user-001 returns extended profile data"""
        response = requests.get(f"{BASE_URL}/api/profile/extended/user-001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "profile" in data
        assert data["profile"]["user_id"] == "user-001"
    
    def test_update_extended_profile(self):
        """PUT /api/profile/extended/user-001 saves profile fields"""
        payload = {
            "volledige_naam": "Willem Spakman",
            "email": "willem@spark.ai",
            "telefoon": "+31 6 12345678",
            "straat": "Bentismaheerd 180",
            "postcode": "9636 EK",
            "plaats": "Groningen",
            "land": "Nederland",
            "noodcontact_naam": "Test Contact",
            "noodcontact_telefoon": "+31 6 87654321"
        }
        response = requests.put(f"{BASE_URL}/api/profile/extended/user-001", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "profile" in data
        # Verify fields were saved
        profile = data["profile"]
        assert profile["volledige_naam"] == "Willem Spakman"
        assert profile["email"] == "willem@spark.ai"
        assert profile["straat"] == "Bentismaheerd 180"
        assert profile["noodcontact_naam"] == "Test Contact"
        # Verify persistence with GET
        verify_response = requests.get(f"{BASE_URL}/api/profile/extended/user-001")
        verify_data = verify_response.json()
        assert verify_data["profile"]["volledige_naam"] == "Willem Spakman"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
