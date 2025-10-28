"""
Integration tests for the queue producer module.
"""

import unittest
from datetime import datetime
from typing import cast, List
from app.ai.queue_producer import IntentQueueProducer, QueuePublishError, IntentScore

class TestIntentQueueProducer(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.producer = IntentQueueProducer()
        
    def test_publish_single_message(self):
        """Test publishing a single message."""
        query = "show me red shoes and add to cart"
        intent_scores: List[IntentScore] = [
            {"intent": 0.7, "score": 0.7},
            {"intent": 0.65, "score": 0.65}
        ]
        
        request_id = self.producer.publish_ambiguous_query(
            query=query,
            intent_scores=cast(List[IntentScore], intent_scores)
        )
        
        self.assertIsNotNone(request_id)
        self.assertTrue(len(request_id) > 0)
        
    def test_batch_publishing(self):
        """Test batch publishing functionality."""
        producer = IntentQueueProducer({
            'batch_size': 2,
            'batch_timeout': 60
        })
        
        # Publish two messages to trigger batch
        intent_score: IntentScore = {"intent": 0.5, "score": 0.5}
        for i in range(2):
            request_id = producer.publish_ambiguous_query(
                query=f"test query {i}",
                intent_scores=[intent_score]
            )
            self.assertIsNotNone(request_id)
            
        # Verify batch was cleared
        self.assertEqual(len(producer._message_batch), 0)
        
    def test_priority_message(self):
        """Test publishing a priority message."""
        query = "cancel my order immediately"
        intent_scores: List[IntentScore] = [
            {"intent": 0.6, "score": 0.6},
            {"intent": 0.55, "score": 0.55}
        ]
        
        request_id = self.producer.publish_ambiguous_query(
            query=query,
            intent_scores=intent_scores,
            priority=True
        )
        
        self.assertIsNotNone(request_id)
        
    def test_error_handling(self):
        """Test error handling for publishing failures."""
        # Create a producer that will fail to publish
        class FailingProducer(IntentQueueProducer):
            def _publish_message(self, message, is_batch=False):
                raise Exception("Simulated publish failure")
                
        producer = FailingProducer()
        
        with self.assertRaises(QueuePublishError):
            intent_score: IntentScore = {"intent": 0.5, "score": 0.5}
            producer.publish_ambiguous_query(
                query="test query",
                intent_scores=[intent_score]
            )
            
if __name__ == '__main__':
    unittest.main()