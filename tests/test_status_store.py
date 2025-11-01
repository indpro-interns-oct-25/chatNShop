import unittest
import uuid
from datetime import datetime, timezone
from app.core.status_store import InMemoryStatusStore
from app.schemas.request_status import RequestStatus, ResultSchema


class TestStatusStore(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryStatusStore()

    def test_add_and_get_request_status(self):
        rid = str(uuid.uuid4())
        status_data = RequestStatus(
            request_id=rid,
            status="QUEUED",
            queued_at=datetime.now(timezone.utc)
        )
        self.store.save(status_data)
        fetched = self.store.get(rid)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.request_id, rid)
        self.assertEqual(fetched.status, "QUEUED")

    def test_update_status(self):
        rid = str(uuid.uuid4())
        status_data = RequestStatus(
            request_id=rid,
            status="QUEUED",
            queued_at=datetime.now(timezone.utc)
        )
        self.store.save(status_data)
        self.store.update_status(rid, "PROCESSING")
        updated = self.store.get(rid)
        self.assertEqual(updated.status, "PROCESSING")
        self.assertIsNotNone(updated.started_at)

    def test_complete_request_with_result(self):
        rid = str(uuid.uuid4())
        status_data = RequestStatus(
            request_id=rid,
            status="PROCESSING",
            started_at=datetime.now(timezone.utc)
        )
        self.store.save(status_data)

        # Use the actual ResultSchema fields
        result = ResultSchema(action_code="SEARCH", confidence=0.95, entities={"query": "laptop"})
        self.store.complete_request(rid, result)
        completed = self.store.get(rid)
        self.assertEqual(completed.status, "COMPLETED")
        self.assertIsNotNone(completed.completed_at)
        self.assertIsNotNone(completed.result)
        self.assertEqual(completed.result.action_code, "SEARCH")
        self.assertAlmostEqual(completed.result.confidence, 0.95)


if __name__ == "__main__":
    print("=== Running Status Store Tests ===")
    unittest.main()
