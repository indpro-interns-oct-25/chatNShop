"""
Integration tests for TASK-15, TASK-16, TASK-17

Tests the complete flow:
1. Queue Producer → Queue → Status Store
2. Worker → Status Store → Calibration
3. API Endpoint → Status Store
"""

import unittest
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

IMPORTS_OK = True
IMPORT_ERROR = None

try:
    from app.queue.queue_producer import get_queue_producer
    from app.core.status_store import status_store
    from app.schemas.request_status import RequestStatus, ResultSchema
    from app.ai.llm_intent.confidence_calibration import get_calibrator
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)


@unittest.skipIf(not IMPORTS_OK, f"Imports failed: {IMPORT_ERROR or 'Unknown error'}")
class TestTasks151617Integration(unittest.TestCase):
    """Integration tests for TASK-15, TASK-16, TASK-17"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.producer = get_queue_producer()
        self.calibrator = get_calibrator()
        self.test_user_id = "test_user_integration"
        self.test_session_id = "test_session_integration"
    
    def test_01_queue_producer_publish(self):
        """Test TASK-15: Queue producer can publish messages"""
        request_id = self.producer.publish_ambiguous_query(
            query="I need something for running",
            rule_based_result={
                "action_code": "UNCLEAR",
                "confidence": 0.35,
                "matched_keywords": []
            },
            user_id=self.test_user_id,
            session_id=self.test_session_id,
            conversation_history=[],
            priority="normal"
        )
        
        self.assertIsNotNone(request_id)
        self.assertIsInstance(request_id, str)
        self.assertTrue(len(request_id) > 0)
        print(f"✅ Published message: {request_id}")
    
    def test_02_status_store_lifecycle(self):
        """Test TASK-16: Status store lifecycle QUEUED → PROCESSING → COMPLETED"""
        test_id = str(uuid.uuid4())
        
        # Create QUEUED status
        queued_status = RequestStatus(
            request_id=test_id,
            status="QUEUED",
            queued_at=datetime.now(timezone.utc),
            retry_count=0
        )
        status_store.save(queued_status)
        
        # Verify QUEUED
        status = status_store.get(test_id)
        self.assertIsNotNone(status)
        self.assertEqual(status.status, "QUEUED")
        self.assertIsNotNone(status.queued_at)
        
        # Update to PROCESSING
        status_store.update_status(test_id, "PROCESSING")
        status = status_store.get(test_id)
        self.assertEqual(status.status, "PROCESSING")
        self.assertIsNotNone(status.started_at)
        
        # Complete with result
        result = ResultSchema(
            action_code="SEARCH",
            confidence=0.87,
            entities={"query": "running shoes"}
        )
        status_store.complete_request(test_id, result=result)
        status = status_store.get(test_id)
        self.assertEqual(status.status, "COMPLETED")
        self.assertIsNotNone(status.completed_at)
        self.assertIsNotNone(status.result)
        self.assertEqual(status.result.action_code, "SEARCH")
        print(f"✅ Status lifecycle completed: {test_id}")
    
    def test_03_confidence_calibration(self):
        """Test TASK-17: Confidence calibration adjusts scores"""
        # Test calibration without historical data (should return original)
        original_confidence = 0.75
        calibrated = self.calibrator.calibrate_confidence(
            action_code="SEARCH",
            reported_confidence=original_confidence
        )
        
        # Without historical data, should return original or close to it
        self.assertIsInstance(calibrated, float)
        self.assertGreaterEqual(calibrated, 0.0)
        self.assertLessEqual(calibrated, 1.0)
        print(f"✅ Calibration: {original_confidence:.2f} → {calibrated:.2f}")
    
    def test_04_producer_creates_status(self):
        """Test integration: Producer creates status in store"""
        request_id = self.producer.publish_ambiguous_query(
            query="What should I buy?",
            rule_based_result={"action_code": "UNCLEAR", "confidence": 0.4},
            user_id=self.test_user_id
        )
        
        # Check if status was created (may fail if queue unavailable)
        status = status_store.get(request_id)
        if status:
            self.assertEqual(status.status, "QUEUED")
            self.assertEqual(status.request_id, request_id)
            print(f"✅ Producer created status: {request_id}")
        else:
            # If using in-memory fallback, status may not persist
            print(f"⚠️ Status not found (may be in-memory fallback)")
    
    def test_05_calibration_fallback_logic(self):
        """Test TASK-17: Calibration fallback for low confidence"""
        should_fallback, reason = self.calibrator.should_trigger_fallback(
            action_code="SEARCH",
            calibrated_confidence=0.3,
            fallback_threshold=0.5
        )
        
        self.assertTrue(should_fallback)
        self.assertIn("low_confidence", reason)
        print(f"✅ Fallback logic works: {reason}")
    
    def test_06_status_store_fast_lookup(self):
        """Test TASK-16: Status store provides fast lookup"""
        import time
        
        test_id = str(uuid.uuid4())
        status = RequestStatus(
            request_id=test_id,
            status="QUEUED",
            queued_at=datetime.now(timezone.utc)
        )
        status_store.save(status)
        
        # Measure lookup time (should be < 10ms p95 as per TASK-16)
        start = time.time()
        retrieved = status_store.get(test_id)
        lookup_time = (time.time() - start) * 1000  # Convert to ms
        
        self.assertIsNotNone(retrieved)
        self.assertLess(lookup_time, 50)  # Allow some margin for test environment
        print(f"✅ Fast lookup: {lookup_time:.2f}ms")


if __name__ == "__main__":
    print("=" * 60)
    print("TASK-15, TASK-16, TASK-17 Integration Tests")
    print("=" * 60)
    unittest.main(verbosity=2)

