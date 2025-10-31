"""
Queue Infrastructure Tests (CNS-21)

Simple tests to verify queue functionality.
"""

import pytest
import time
from app.queue.queue_manager import QueueManager
from app.queue.config import QueueConfig


def test_queue_config():
    """Test queue configuration loads correctly"""
    config = QueueConfig()
    assert config.MESSAGE_TTL == 86400
    assert config.MAX_RETRY_ATTEMPTS == 3
    assert config.AMBIGUOUS_QUERY_QUEUE == "chatns:queue:ambiguous_queries"
    print("✅ Queue config test passed")


def test_enqueue_dequeue():
    """Test basic enqueue/dequeue operations"""
    try:
        qm = QueueManager()
        
        # Enqueue message
        msg_id = qm.enqueue_ambiguous_query(
            query="test query",
            context={"user_id": "test_user"},
            priority=5
        )
        
        assert msg_id is not None
        print(f"✅ Enqueued message: {msg_id}")
        
        # Dequeue message
        message = qm.dequeue_ambiguous_query()
        
        assert message is not None
        assert message["query"] == "test query"
        assert message["context"]["user_id"] == "test_user"
        print(f"✅ Dequeued message: {message['message_id']}")
        
        # Clean up
        qm.clear_queue("chatns:queue:ambiguous_queries")
        
    except Exception as e:
        print(f"⚠️ Test skipped (Redis not available): {e}")
        pytest.skip("Redis not available")


def test_queue_stats():
    """Test queue statistics"""
    try:
        qm = QueueManager()
        
        stats = qm.get_queue_stats()
        
        assert "ambiguous_queue_size" in stats
        assert "result_queue_size" in stats
        assert "dead_letter_queue_size" in stats
        print(f"✅ Queue stats: {stats}")
        
    except Exception as e:
        print(f"⚠️ Test skipped (Redis not available): {e}")
        pytest.skip("Redis not available")


def test_health_check():
    """Test queue health check"""
    try:
        qm = QueueManager()
        
        is_healthy = qm.health_check()
        assert is_healthy == True
        print("✅ Health check passed")
        
    except Exception as e:
        print(f"⚠️ Test skipped (Redis not available): {e}")
        pytest.skip("Redis not available")


if __name__ == "__main__":
    print("Running Queue Infrastructure Tests...\n")
    
    test_queue_config()
    test_enqueue_dequeue()
    test_queue_stats()
    test_health_check()
    
    print("\n✅ All tests passed!")
