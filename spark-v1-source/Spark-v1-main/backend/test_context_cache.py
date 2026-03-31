"""
Unit tests voor ContextCache

Test alle cache functionaliteit:
- Basic operations (get, add, has)
- LRU eviction
- Session cleanup
- Statistics
- Memory estimation
"""
from services.context_cache import ContextCache, CachedMessage, get_cache, reset_cache
from datetime import datetime, timedelta, timezone
import time


def test_basic_operations():
    """Test basic cache operations"""
    print("\n" + "="*60)
    print("TEST 1: Basic Operations")
    print("="*60)
    
    cache = ContextCache(max_sessions=5, messages_per_session=3)
    
    # Test 1: Cache miss
    result = cache.get("session_1")
    assert result is None, "Expected cache miss"
    assert cache.misses == 1, "Miss count should be 1"
    print("✓ Cache miss works correctly")
    
    # Test 2: Add message
    msg1 = CachedMessage(
        message="Hello",
        sender="user",
        timestamp=datetime.now(timezone.utc),
        session_id="session_1",
        emotion="happy",
        topics=["greeting"],
        sentiment="positief"
    )
    cache.add_message("session_1", msg1)
    assert cache.has_session("session_1"), "Session should exist"
    assert cache.get_session_count("session_1") == 1, "Should have 1 message"
    print("✓ Add message works correctly")
    
    # Test 3: Cache hit
    result = cache.get("session_1")
    assert result is not None, "Expected cache hit"
    assert len(result) == 1, "Should return 1 message"
    assert result[0].message == "Hello", "Message content should match"
    assert cache.hits == 1, "Hit count should be 1"
    print("✓ Cache hit works correctly")
    
    # Test 4: Multiple messages
    msg2 = CachedMessage(
        message="How are you?",
        sender="user",
        timestamp=datetime.now(timezone.utc),
        session_id="session_1",
        intent="question"
    )
    cache.add_message("session_1", msg2)
    assert cache.get_session_count("session_1") == 2, "Should have 2 messages"
    print("✓ Multiple messages work correctly")
    
    # Test 5: Max messages per session
    msg3 = CachedMessage("Message 3", "user", datetime.now(timezone.utc), "session_1")
    msg4 = CachedMessage("Message 4", "user", datetime.now(timezone.utc), "session_1")
    cache.add_message("session_1", msg3)
    cache.add_message("session_1", msg4)
    
    # Should only keep last 3 messages (max_messages=3)
    assert cache.get_session_count("session_1") == 3, "Should cap at 3 messages"
    messages = cache.get("session_1")
    assert messages[0].message == "How are you?", "Oldest message should be evicted"
    print("✓ Max messages per session works correctly")
    
    print("\n✅ All basic operations tests passed!")


def test_lru_eviction():
    """Test LRU eviction policy"""
    print("\n" + "="*60)
    print("TEST 2: LRU Eviction")
    print("="*60)
    
    cache = ContextCache(max_sessions=3, messages_per_session=5)
    
    # Add 3 sessions
    for i in range(1, 4):
        msg = CachedMessage(
            f"Message {i}",
            "user",
            datetime.now(timezone.utc),
            f"session_{i}"
        )
        cache.add_message(f"session_{i}", msg)
    
    assert len(cache._cache) == 3, "Should have 3 sessions"
    print("✓ Added 3 sessions")
    
    # Access session_1 (make it most recent)
    cache.get("session_1")
    
    # Add 4th session (should evict session_2, the oldest unused)
    msg4 = CachedMessage("Message 4", "user", datetime.now(timezone.utc), "session_4")
    cache.add_message("session_4", msg4)
    
    assert len(cache._cache) == 3, "Should still have 3 sessions"
    assert not cache.has_session("session_2"), "session_2 should be evicted (LRU)"
    assert cache.has_session("session_1"), "session_1 should still exist (recently accessed)"
    assert cache.has_session("session_3"), "session_3 should still exist"
    assert cache.has_session("session_4"), "session_4 should exist (just added)"
    print("✓ LRU eviction works correctly")
    
    print("\n✅ LRU eviction test passed!")


def test_session_cleanup():
    """Test old session cleanup"""
    print("\n" + "="*60)
    print("TEST 3: Session Cleanup")
    print("="*60)
    
    cache = ContextCache(max_sessions=10, messages_per_session=5)
    
    # Add old message (25 hours ago)
    old_time = datetime.now(timezone.utc) - timedelta(hours=25)
    old_msg = CachedMessage("Old message", "user", old_time, "old_session")
    cache.add_message("old_session", old_msg)
    
    # Add recent message (1 hour ago)
    recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
    recent_msg = CachedMessage("Recent message", "user", recent_time, "recent_session")
    cache.add_message("recent_session", recent_msg)
    
    print(f"Before cleanup: {len(cache._cache)} sessions")
    
    # Cleanup sessions older than 24 hours
    removed = cache.clear_old_sessions(max_age_hours=24)
    
    print(f"After cleanup: {len(cache._cache)} sessions")
    print(f"Removed: {removed} sessions")
    
    assert removed == 1, "Should remove 1 old session"
    assert not cache.has_session("old_session"), "Old session should be removed"
    assert cache.has_session("recent_session"), "Recent session should remain"
    print("✓ Session cleanup works correctly")
    
    print("\n✅ Session cleanup test passed!")


def test_statistics():
    """Test statistics tracking"""
    print("\n" + "="*60)
    print("TEST 4: Statistics")
    print("="*60)
    
    cache = ContextCache(max_sessions=5, messages_per_session=10)
    
    # Generate some activity
    cache.get("session_1")  # miss
    cache.add_message("session_1", CachedMessage("msg1", "user", datetime.now(timezone.utc), "session_1"))
    cache.get("session_1")  # hit
    cache.get("session_1")  # hit
    cache.get("session_2")  # miss
    
    stats = cache.get_stats()
    
    print("\nCache Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    assert stats["hits"] == 2, "Should have 2 hits"
    assert stats["misses"] == 2, "Should have 2 misses"
    assert stats["hit_rate_percent"] == 50.0, "Hit rate should be 50%"
    assert stats["active_sessions"] == 1, "Should have 1 active session"
    assert stats["total_messages"] == 1, "Should have 1 total message"
    print("\n✓ Statistics tracking works correctly")
    
    print("\n✅ Statistics test passed!")


def test_memory_estimation():
    """Test memory usage estimation"""
    print("\n" + "="*60)
    print("TEST 5: Memory Estimation")
    print("="*60)
    
    cache = ContextCache(max_sessions=100, messages_per_session=20)
    
    # Add many messages
    for session in range(10):
        for msg_num in range(15):
            msg = CachedMessage(
                f"This is a test message number {msg_num} for session {session}",
                "user",
                datetime.now(timezone.utc),
                f"session_{session}",
                emotion="neutral",
                topics=["test", "memory"],
                sentiment="neutraal"
            )
            cache.add_message(f"session_{session}", msg)
    
    stats = cache.get_stats()
    memory_mb = stats["memory_usage_mb"]
    
    print(f"\nMemory Usage:")
    print(f"  Sessions: {stats['active_sessions']}")
    print(f"  Total Messages: {stats['total_messages']}")
    print(f"  Estimated Memory: {memory_mb} MB")
    
    # Sanity check: should be reasonable (< 5 MB for 150 messages)
    assert memory_mb < 5.0, "Memory usage should be reasonable"
    assert memory_mb > 0.0, "Memory usage should be positive"
    print("\n✓ Memory estimation is reasonable")
    
    print("\n✅ Memory estimation test passed!")


def test_global_singleton():
    """Test global singleton instance"""
    print("\n" + "="*60)
    print("TEST 6: Global Singleton")
    print("="*60)
    
    # Reset to clean state
    reset_cache()
    
    # Get cache twice
    cache1 = get_cache()
    cache2 = get_cache()
    
    assert cache1 is cache2, "Should return same instance"
    print("✓ Singleton pattern works correctly")
    
    # Add message to cache1
    msg = CachedMessage("Test", "user", datetime.now(timezone.utc), "test_session")
    cache1.add_message("test_session", msg)
    
    # Should be visible in cache2
    assert cache2.has_session("test_session"), "Changes should be visible across instances"
    print("✓ State is shared across singleton instances")
    
    print("\n✅ Global singleton test passed!")


def test_dict_conversion():
    """Test conversion to dicts for backward compatibility"""
    print("\n" + "="*60)
    print("TEST 7: Dict Conversion")
    print("="*60)
    
    cache = ContextCache()
    
    msg = CachedMessage(
        message="Hello World",
        sender="user",
        timestamp=datetime.now(timezone.utc),
        session_id="test_session",
        emotion="happy",
        topics=["greeting", "test"],
        sentiment="positief",
        intent="greeting"
    )
    cache.add_message("test_session", msg)
    
    # Get as dicts
    dicts = cache.get_session_messages_as_dicts("test_session")
    
    assert len(dicts) == 1, "Should have 1 message"
    assert dicts[0]["message"] == "Hello World", "Message should match"
    assert dicts[0]["sender"] == "user", "Sender should match"
    assert dicts[0]["emotion"] == "happy", "Emotion should match"
    assert dicts[0]["topics"] == ["greeting", "test"], "Topics should match"
    print("✓ Dict conversion works correctly")
    
    print("\n✅ Dict conversion test passed!")


def run_all_tests():
    """Run all cache tests"""
    print("\n" + "#"*60)
    print("# CONTEXT CACHE TEST SUITE")
    print("#"*60)
    
    start_time = time.time()
    
    try:
        test_basic_operations()
        test_lru_eviction()
        test_session_cleanup()
        test_statistics()
        test_memory_estimation()
        test_global_singleton()
        test_dict_conversion()
        
        elapsed = time.time() - start_time
        
        print("\n" + "#"*60)
        print(f"# ✅ ALL TESTS PASSED ({elapsed:.2f}s)")
        print("#"*60)
        print("\nContext Cache is ready for production use!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
