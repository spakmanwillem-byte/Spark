"""
Integration test - Test Content Engine vanuit spark_brain.py context

Dit test of de Content Engine correct gebruikt kan worden
in de bestaande codebase structuur.
"""
from services.content_engine import ContentEngine, ContentAnalysis

def test_integration():
    """Test integratie met bestaande services"""
    
    print("=" * 60)
    print("CONTENT ENGINE INTEGRATION TEST")
    print("=" * 60)
    
    # Simuleer gebruik zoals in spark_brain.py
    engine = ContentEngine()
    
    # Test met verschillende berichten
    test_cases = [
        {
            "message": "Wat is de betekenis van leven?",
            "user_data": {"id": "test_user", "naam": "Willem"}
        },
        {
            "message": "Bedankt voor je hulp!",
            "user_data": {"id": "test_user", "naam": "Willem"}
        },
        {
            "message": "Leer jezelf: de hoofdstad van Nederland is Amsterdam",
            "user_data": {"id": "test_user", "naam": "Willem"}
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i}")
        print(f"{'='*60}")
        print(f"Message: {test['message']}")
        print(f"User: {test['user_data']['naam']}")
        
        # Analyseer met Content Engine
        analysis: ContentAnalysis = engine.analyze(
            text=test['message'],
            user_data=test['user_data']
        )
        
        # Toon belangrijke resultaten
        print(f"\n📊 Analysis Results:")
        print(f"  Intent: {analysis.intent.primary_intent}")
        print(f"  Tone: {analysis.tone}")
        print(f"  Sentiment: {analysis.sentiment}")
        print(f"  Topic: {analysis.primary_topic or 'none'}")
        print(f"  Has Compliment: {analysis.compliments.has_compliment}")
        print(f"  Is Question: {analysis.intent.is_question}")
        print(f"  Is Teaching: {analysis.intent.is_teaching}")
        print(f"  Confidence: {analysis.confidence:.2f}")
        
        # Test dataclass access
        print(f"\n🔍 Detailed Access:")
        print(f"  Language Style - Formality: {analysis.language_style.formality_level:.2f}")
        print(f"  Language Style - Intensity: {analysis.language_style.emotional_intensity:.2f}")
        print(f"  Keywords - Topics: {', '.join(analysis.keywords.topics) or 'none'}")
        print(f"  Keywords - Primary: {', '.join(analysis.keywords.primary_keywords[:3])}")
        
        # Test dat alle properties beschikbaar zijn
        assert hasattr(analysis, 'text')
        assert hasattr(analysis, 'language_style')
        assert hasattr(analysis, 'intent')
        assert hasattr(analysis, 'keywords')
        assert hasattr(analysis, 'compliments')
        assert isinstance(analysis.confidence, float)
        assert isinstance(analysis.processing_time_ms, int)
        
        print(f"\n✅ All properties accessible")
    
    print(f"\n{'='*60}")
    print("✅ INTEGRATION TEST PASSED")
    print("Content Engine is ready for use in spark_brain.py")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_integration()
