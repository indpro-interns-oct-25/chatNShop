import unittest
from app.ai.queue_producer import IntentQueueProducer, QueuePublishError


class TestQueueProducer(unittest.TestCase):

    def test_publish_message_format_and_priority(self):
        prod = IntentQueueProducer(queue_config={"batch_size": 1})
        captured = {}

        # parameter name matches the typed attribute: "message"
        def fake_publish(message, is_batch: bool = False) -> None:
            captured['msg'] = message
            captured['is_batch'] = is_batch

        prod._publish_message = fake_publish

        req_id = prod.publish_ambiguous_query(
            query="I need something for running",
            intent_scores=[{"intent": "SEARCH_PRODUCT", "score": 0.45}],
            priority=True,
            metadata={"foo": "bar"},
            session_id="session-123",
            user_id="user-456",
            conversation_history=[{"turn": "user", "text": "hi"}],
            rule_based_result={"action_code": "UNCLEAR", "confidence": 0.45, "matched_keywords": []}
        )
        self.assertIsInstance(req_id, str)
        # allow background worker a moment to process
        import time
        time.sleep(0.05)
        self.assertIn('msg', captured)
        msg = captured['msg']
        # verify spec fields
        self.assertEqual(msg['request_id'], req_id)
        self.assertEqual(msg['user_query'], "I need something for running")
        self.assertEqual(msg['session_id'], "session-123")
        self.assertEqual(msg['user_id'], "user-456")
        self.assertEqual(msg['priority'], 'high')
        self.assertIn('timestamp', msg)
        self.assertIn('rule_based_result', msg)
        self.assertIn('metadata', msg)
        # metadata should contain intent_scores
        self.assertIn('intent_scores', msg['metadata'])

    def test_batching_triggers_publish(self):
        prod = IntentQueueProducer(queue_config={"batch_size": 2})
        published = []

        # parameter name matches the typed attribute: "message"
        def fake_publish(message, is_batch: bool = False) -> None:
            published.append((message, is_batch))

        prod._publish_message = fake_publish

        # first message should be batched and not published yet
        id1 = prod.publish_ambiguous_query(
            query="first",
            intent_scores=[],
            priority=False
        )
        # give worker a small window -- it should not publish until batch size reached
        import time
        time.sleep(0.02)
        self.assertEqual(len(published), 0)

        # second message should trigger batch publish
        id2 = prod.publish_ambiguous_query(
            query="second",
            intent_scores=[],
            priority=False
        )
        # should have published one batch (allow worker to process)
        import time
        time.sleep(0.05)
        self.assertEqual(len(published), 1)
        batch_msg, is_batch = published[0]
        self.assertTrue(is_batch)
        self.assertIn('batch_id', batch_msg)
        self.assertIn('messages', batch_msg)
        self.assertEqual(len(batch_msg['messages']), 2)

    def test_publish_error_is_handled(self):
        prod = IntentQueueProducer(queue_config={"batch_size": 1})

        # parameter name matches the typed attribute: "message"
        def fake_publish_raises(message, is_batch: bool = False) -> None:
            raise Exception("boom")

        prod._publish_message = fake_publish_raises

        # With async publishing, exceptions from the worker should not be raised to caller.
        # publish_ambiguous_query should return a request id immediately even if publish later fails.
        req = prod.publish_ambiguous_query(
            query="will fail",
            intent_scores=[],
            priority=False
        )
        self.assertIsInstance(req, str)
        # allow worker to run and observe that the fake publish raised; nothing should bubble up
        import time
        time.sleep(0.05)


if __name__ == '__main__':
    unittest.main()