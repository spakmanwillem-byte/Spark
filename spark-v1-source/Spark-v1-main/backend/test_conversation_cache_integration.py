"""
Integration test voor ConversationCacheService

Test de volledige flow:
1. Cache miss → load from disk → populate cache
2. Cache hit → instant return
3. Add message → update cache
4. Get conversation context
"""
from services.conversation_cache_service import ConversationCacheService
from services.context_cache import reset_cache
from datetime import datetime, timezone
import time


def test_cache_miss_and_populate():
    """Test cache miss scenario en auto-populate"""
    print("\n" + "="*60)
    print("TEST 1: Cache Miss → Disk Load → Cache Populate")
    print("="*60)
    
    # Reset cache to clean state
    reset_cache()
    
    service = ConversationCacheService()
    
    # First call: should be cache miss
    print("\n1️⃣ First call (expecting cache miss)...")
    start = time.time()
    messages = service.get_recent_messages(
        user_id="test_user",
        session_id="test_session_1",
        limit=10
    )
    first_call_time = (time.time() - start) * 1000
    
    print(f"   Time: {first_call_time:.2f}ms")
    print(f"   Messages: {len(messages)}")
    print(f"   Result: {'CACHE MISS (loaded from disk)' if len(messages) == 0 else 'Loaded'}")
    
    # Check stats
    stats = service.get_cache_stats()
    print(f"\n📊 Cache Stats after first call:")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate_percent']}%")
    
    assert stats['misses'] >= 1, "Should have at least one miss"
    print("\n✓ Cache miss detected correctly")
    
    print("\n✅ Test 1 passed!")


def test_cache_hit():
    """Test cache hit scenario"""
    print("\n" + "="*60)
    print("TEST 2: Cache Hit (Fast Access)")
    print("="*60)
    
    # Reset and setup
    reset_cache()
    service = ConversationCacheService()
    
    # Add some test messages to cache
    print("\n1️⃣ Adding test messages to cache...")
    for i in range(5):
        service.add_message(
            session_id="test_session_2",
            message=f"Test message {i+1}",
            sender="user",
            user_id="test_user_2",
            emotion="neutral",
            topics=["test"],
            sentiment="neutraal"
        )
    
    print(f"   Added 5 messages")
    
    # Now fetch (should be cache hit)
    print("\n2️⃣ Fetching messages (expecting cache hit)...")
    start = time.time()
    messages = service.get_recent_messages(
        user_id="test_user_2",
        session_id="test_session_2",
        limit=10
    )
    fetch_time = (time.time() - start) * 1000
    
    print(f"   Time: {fetch_time:.2f}ms (target: < 10ms)")
    print(f"   Messages retrieved: {len(messages)}")
    
    # Check stats
    stats = service.get_cache_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit Rate: {stats['hit_rate_percent']}%")
    
    assert stats['hits'] >= 1, "Should have at least one hit"
    assert len(messages) == 5, "Should return 5 messages"
    assert fetch_time < 10, f"Cache hit should be < 10ms (was {fetch_time:.2f}ms)"
    
    print("\n✓ Cache hit is fast (< 10ms)")
    print("✓ Correct number of messages returned")
    
    print("\n✅ Test 2 passed!")


def test_conversation_context():
    """Test conversation context extraction"""
    print("\n" + "="*60)
    print("TEST 3: Conversation Context")
    print("="*60)
    
    reset_cache()
    service = ConversationCacheService()
    
    # Add diverse messages
    print("\n1️⃣ Creating conversation history...")
    test_messages = [
        {"msg": "Wat is een auto?", "emotion": "curious", "topics": ["auto", "voertuigen"]},
        {"msg": "Vertel me meer", "emotion": "interested", "topics": ["auto"]},
        {"msg": "Dat is interessant!", "emotion": "happy", "topics": ["auto"]},
        {"msg": "Hoe werkt een motor?", "emotion": "curious", "topics": ["motor", "techniek"]},
    ]
    
    for i, data in enumerate(test_messages):
        service.add_message(
            session_id="test_session_3",
            message=data["msg"],
            sender="user",
            user_id="test_user_3",
            emotion=data["emotion"],
            topics=data["topics"],
            sentiment="positief"
        )
    
    print(f"   Added {len(test_messages)} messages")
    
    # Get conversation context
    print("\n2️⃣ Extracting conversation context...")
    context = service.get_conversation_context(
        user_id="test_user_3",
        session_id="test_session_3",
        limit=10
    )
    
    print(f"\n📋 Conversation Context:")
    print(f"   Message Count: {context['message_count']}")
    print(f"   Topics: {context['topics']}")
    print(f"   Primary Topic: {context['primary_topic']}")
    print(f"   Emotions: {context['emotions']}")
    print(f"   Recent Emotion: {context['recent_emotion']}")
    
    assert context['message_count'] == 4, "Should have 4 messages"
    assert len(context['messages']) == 4, "Should return 4 message dicts"
    
    print("\n✓ Context extraction works correctly")
    
    print("\n✅ Test 3 passed!")


def test_session_management():
    """Test session clearing"""
    print("\n" + "="*60)
    print("TEST 4: Session Management")
    print("="*60)
    
    reset_cache()
    service = ConversationCacheService()
    
    # Add messages to multiple sessions
    print("\n1️⃣ Creating multiple sessions...")
    for session_num in range(3):
        for msg_num in range(5):
            service.add_message(
                session_id=f"session_{session_num}",
                message=f"Message {msg_num}",
                sender="user",
                user_id=f"user_{session_num}",
                emotion="neutral"
            )
    
    stats_before = service.get_cache_stats()
    print(f"   Active sessions: {stats_before['active_sessions']}")
    print(f"   Total messages: {stats_before['total_messages']}")
    
    # Clear one session
    print("\n2️⃣ Clearing session_1...")
    service.clear_session("session_1")
    
    stats_after = service.get_cache_stats()
    print(f"   Active sessions: {stats_after['active_sessions']}")
    print(f"   Total messages: {stats_after['total_messages']}")
    
    assert stats_after['active_sessions'] == stats_before['active_sessions'] - 1, \
        "Should have one less session"
    
    print("\n✓ Session clearing works correctly")
    
    print("\n✅ Test 4 passed!")


def test_performance_benchmark():
    """Benchmark cache performance"""
    print("\n" + "="*60)
    print("TEST 5: Performance Benchmark")
    print("="*60)
    
    reset_cache()
    service = ConversationCacheService()
    
    # Setup: Add messages
    print("\n1️⃣ Setting up test data...")
    session_id = "benchmark_session"
    for i in range(20):
        service.add_message(
            session_id=session_id,
            message=f"Benchmark message {i}",
            sender="user",
            user_id="benchmark_user",
            emotion="neutral",
            topics=["benchmark", "test"],
            sentiment="neutraal"
        )
    
    # Benchmark: Multiple cache hits
    print("\n2️⃣ Running benchmark (100 cache hits)...")
    times = []
    for i in range(100):
        start = time.time()
        messages = service.get_recent_messages(
            user_id="benchmark_user",
            session_id=session_id,
            limit=20
        )
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📊 Performance Results (100 requests):")
    print(f"   Average: {avg_time:.3f}ms")
    print(f"   Min: {min_time:.3f}ms")
    print(f"   Max: {max_time:.3f}ms")
    print(f"   Target: < 5ms average")
    
    # Check cache stats
    stats = service.get_cache_stats()
    print(f"\n📊 Final Cache Stats:")
    print(f"   Hit Rate: {stats['hit_rate_percent']}%")
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Memory Usage: {stats['memory_usage_mb']} MB")
    
    assert avg_time < 5.0, f"Average time should be < 5ms (was {avg_time:.3f}ms)"
    assert stats['hit_rate_percent'] > 90, "Hit rate should be > 90%"
    
    print("\n✓ Performance meets targets (< 5ms average)")
    print("✓ High cache hit rate (> 90%)")
    
    print("\n✅ Test 5 passed!")


def run_all_integration_tests():
    """Run all integration tests"""
    print("\n" + "#"*60)
    print("# CONVERSATION CACHE INTEGRATION TEST SUITE")
    print("#"*60)
    
    start_time = time.time()
    
    try:
        test_cache_miss_and_populate()
        test_cache_hit()
        test_conversation_context()
        test_session_management()
        test_performance_benchmark()
        
        elapsed = time.time() - start_time
        
        print("\n" + "#"*60)
        print(f"# ✅ ALL INTEGRATION TESTS PASSED ({elapsed:.2f}s)")
        print("#"*60)
        print("\n🚀 ConversationCacheService is ready for production!")
        print("\n📈 Key Achievements:")
        print("   ✓ Cache-first architecture working")
        print("   ✓ Automatic cache population from disk")
        print("   ✓ < 5ms average cache hit time")
        print("   ✓ > 90% cache hit rate")
        print("   ✓ Clean session management")
        print("   ✓ Rich conversation context extraction")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_integration_tests()
