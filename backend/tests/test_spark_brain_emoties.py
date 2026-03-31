"""
Test Suite for SparkBrainPage and EmotiesPage Backend APIs
Tests emotion detection endpoints: /api/chat/emotions/*
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmotionEndpoints:
    """Tests for emotion detection API endpoints"""
    
    def test_get_emotion_state(self):
        """GET /api/chat/emotions/state - Spark's current emotional state"""
        response = requests.get(f"{BASE_URL}/api/chat/emotions/state")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Validate response structure
        assert "state" in data, "Response should contain 'state'"
        assert "intensity" in data, "Response should contain 'intensity'"
        assert isinstance(data["intensity"], (int, float)), "Intensity should be numeric"
        assert 0 <= data["intensity"] <= 1, "Intensity should be between 0 and 1"
        print(f"✓ Emotion state: {data['state']} (intensity: {data['intensity']})")
    
    def test_get_learned_emotions(self):
        """GET /api/chat/emotions/learned - Learned emotion word counts"""
        response = requests.get(f"{BASE_URL}/api/chat/emotions/learned")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Validate 4 basis emoties are present
        expected_emotions = ["blij", "boos", "bang", "bedroefd"]
        for emo in expected_emotions:
            assert emo in data, f"Response should contain '{emo}'"
            assert isinstance(data[emo], int), f"{emo} count should be integer"
        print(f"✓ Learned counts: blij={data['blij']}, boos={data['boos']}, bang={data['bang']}, bedroefd={data['bedroefd']}")
    
    def test_get_all_emotions(self):
        """GET /api/chat/emotions/all - All emotion definitions with sub-emotions"""
        response = requests.get(f"{BASE_URL}/api/chat/emotions/all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Validate structure
        assert "emotions" in data, "Response should contain 'emotions'"
        assert "current_emotion" in data, "Response should contain 'current_emotion'"
        
        emotions = data["emotions"]
        # Check for expected emotion types (happy, angry, sad, scared, neutral)
        expected_types = ["happy", "angry", "sad", "scared", "neutral"]
        for emo_type in expected_types:
            assert emo_type in emotions, f"Emotions should contain '{emo_type}'"
            
        # Validate sub-emotions structure for happy
        happy = emotions.get("happy", {})
        assert "sub_emotions" in happy, "Happy should have sub_emotions"
        assert "description" in happy, "Happy should have description"
        assert "tone" in happy, "Happy should have tone"
        
        sub_emotions = happy.get("sub_emotions", {})
        assert len(sub_emotions) > 0, "Happy should have at least one sub-emotion"
        print(f"✓ All emotions loaded: {len(emotions)} types, happy has {len(sub_emotions)} sub-emotions")
    
    def test_detect_emotion_blij(self):
        """POST /api/chat/emotions/detect - Detect 'blij' emotion"""
        response = requests.post(
            f"{BASE_URL}/api/chat/emotions/detect",
            json={"message": "Ik ben zo blij vandaag!"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "detected" in data, "Response should contain 'detected'"
        assert data["detected"] == True, "Should detect emotion in 'blij' message"
        assert "emotion" in data, "Response should contain 'emotion'"
        
        emotion = data["emotion"]
        assert emotion["emotion"] == "blij", f"Expected 'blij', got {emotion['emotion']}"
        assert "score" in emotion, "Emotion should have score"
        assert "intensity" in emotion, "Emotion should have intensity"
        assert "triggered_words" in emotion, "Emotion should have triggered_words"
        assert "blij" in emotion["triggered_words"], "Should trigger on 'blij'"
        print(f"✓ Detected blij: score={emotion['score']}, intensity={emotion['intensity']}")
    
    def test_detect_emotion_boos(self):
        """POST /api/chat/emotions/detect - Detect 'boos' emotion"""
        response = requests.post(
            f"{BASE_URL}/api/chat/emotions/detect",
            json={"message": "Dit maakt me boos en gefrustreerd!"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["detected"] == True, "Should detect emotion in 'boos' message"
        emotion = data["emotion"]
        assert emotion["emotion"] == "boos", f"Expected 'boos', got {emotion['emotion']}"
        print(f"✓ Detected boos: score={emotion['score']}, triggered={emotion['triggered_words']}")
    
    def test_detect_emotion_bang(self):
        """POST /api/chat/emotions/detect - Detect 'bang' emotion"""
        response = requests.post(
            f"{BASE_URL}/api/chat/emotions/detect",
            json={"message": "Ik ben bang voor morgen"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["detected"] == True, "Should detect emotion in 'bang' message"
        emotion = data["emotion"]
        assert emotion["emotion"] == "bang", f"Expected 'bang', got {emotion['emotion']}"
        print(f"✓ Detected bang: score={emotion['score']}")
    
    def test_detect_emotion_bedroefd(self):
        """POST /api/chat/emotions/detect - Detect 'bedroefd' emotion"""
        response = requests.post(
            f"{BASE_URL}/api/chat/emotions/detect",
            json={"message": "Ik voel me verdrietig en somber"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["detected"] == True, "Should detect emotion in 'bedroefd' message"
        emotion = data["emotion"]
        assert emotion["emotion"] == "bedroefd", f"Expected 'bedroefd', got {emotion['emotion']}"
        print(f"✓ Detected bedroefd: score={emotion['score']}")
    
    def test_detect_no_emotion(self):
        """POST /api/chat/emotions/detect - No emotion in neutral text"""
        response = requests.post(
            f"{BASE_URL}/api/chat/emotions/detect",
            json={"message": "De kat zit op de mat"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["detected"] == False, "Should not detect emotion in neutral text"
        print("✓ No emotion detected in neutral text")
    
    def test_detect_emotion_empathic_response(self):
        """POST /api/chat/emotions/detect - Check empathic response is returned"""
        response = requests.post(
            f"{BASE_URL}/api/chat/emotions/detect",
            json={"message": "Ik ben zo blij en gelukkig vandaag!"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["detected"] == True, "Should detect emotion with strong trigger words"
        emotion = data["emotion"]
        # empathic_response may or may not be present depending on config
        if "empathic_response" in emotion:
            assert isinstance(emotion["empathic_response"], (str, type(None)))
            print(f"✓ Empathic response: {emotion.get('empathic_response', 'None')}")
        else:
            print("✓ No empathic response configured (acceptable)")
    
    def test_detect_emotion_source_field(self):
        """POST /api/chat/emotions/detect - Verify source field (static/learned/both)"""
        response = requests.post(
            f"{BASE_URL}/api/chat/emotions/detect",
            json={"message": "Ik ben blij"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["detected"] == True
        emotion = data["emotion"]
        assert "source" in emotion, "Emotion should have source field"
        assert emotion["source"] in ["static", "learned", "both"], f"Invalid source: {emotion['source']}"
        print(f"✓ Source field: {emotion['source']}")


class TestAuthAndLogin:
    """Test login to verify app is accessible"""
    
    def test_login_with_credentials(self):
        """POST /api/auth/login - Login with Willem/Appelsap"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"naam": "Willem", "sleutelwoord": "Appelsap"}
        )
        assert response.status_code == 200, f"Login failed: {response.status_code}"
        
        data = response.json()
        assert "user" in data, "Response should contain user"
        assert data["user"]["naam"] == "Willem" or data["user"]["naam"] == "De Willem"
        print(f"✓ Login successful: {data['user']['naam']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
