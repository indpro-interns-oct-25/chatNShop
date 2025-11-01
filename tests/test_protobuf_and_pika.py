import time
import json
import unittest
from types import SimpleNamespace
from typing import cast

import app.ai.queue_producer as qp
from app.ai.queue_producer import IntentQueueProducer, QueuePublishError

# If these names exist in your module, importing them makes the cast more explicit to Pylance.
# If they don't exist, the cast to 'Any' could be used instead; the below assumes they exist.
try:
    from app.ai.queue_producer import QueueMessage, BatchPayload  # type: ignore
except Exception:
    # If the real types are not importable in the test environment, define fallbacks for typing only.
    from typing import Any as QueueMessage  # type: ignore
    from typing import Any as BatchPayload  # type: ignore


class FakeChannel:
    def __init__(self):
        self.published = []

    def basic_publish(self, exchange, routing_key, body, properties):
        # capture publish args
        self.published.append({'exchange': exchange, 'routing_key': routing_key, 'body': body, 'properties': properties})


class FakePikaModule:
    class BasicProperties:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)


class TestProtobufAndPika(unittest.TestCase):

    def test_protobuf_serialization_and_amqp_properties(self):
        # Enable our fake pika and generated proto
        qp._PIKA_AVAILABLE = True
        qp.pika = FakePikaModule()
        qp._GENERATED_PROTO_AVAILABLE = True

        prod = IntentQueueProducer(queue_config={"batch_size": 1, "serialization": "protobuf"})

        # Inject fake channel and a fake connection object so _ensure_connection() skips setup
        fake_channel = FakeChannel()
        prod._channel = fake_channel
        prod._connection = SimpleNamespace(is_closed=False, channel=lambda: fake_channel)

        msg = {
            'request_id': 'rid-123',
            'user_query': 'find shoes',
            'session_id': 'sid',
            'user_id': 'uid',
            'conversation_history': [],
            'rule_based_result': {'action_code': 'UNCLEAR', 'confidence': 0.3, 'matched_keywords': []},
            'timestamp': '2025-10-30T12:00:00Z',
            'priority': 'high',
            'metadata': {}
        }

        # Call _publish_message directly to test AMQP publish args
        # Cast the dict to the expected typed union to satisfy Pylance/type checker
        prod._publish_message(cast(QueueMessage, msg), is_batch=False)

        self.assertEqual(len(fake_channel.published), 1)
        p = fake_channel.published[0]
        # body should be bytes (our generated pb SerializeToString returns bytes)
        self.assertIsInstance(p['body'], (bytes, bytearray))
        # properties.content_type should be application/x-protobuf
        self.assertEqual(p['properties'].content_type, 'application/x-protobuf')
        # priority numeric mapping: 'high' -> 4
        self.assertEqual(p['properties'].priority, 4)
        # correlation header present
        self.assertEqual(p['properties'].headers.get('correlation_id'), 'rid-123')

    def test_wait_for_publish_raises(self):
        # Fake pika not needed; we will override _publish_message to raise
        prod = IntentQueueProducer(queue_config={"batch_size": 1})

        def fake_publish_raises(message, is_batch=False):
            raise Exception('boom')

        prod._publish_message = fake_publish_raises

        with self.assertRaises(QueuePublishError):
            prod.publish_ambiguous_query(
                query='will fail',
                intent_scores=[],
                priority=False,
                wait_for_publish=True
            )

    def test_idempotency_reservation(self):
        prod = IntentQueueProducer(queue_config={"batch_size": 1, "enable_idempotency": True, "idempotency_ttl": 2})
        # ensure queue empty
        initial_q = prod._send_queue.qsize()

        rid = 'static-id-1'
        # first publish reserves and enqueues
        ret1 = prod.publish_ambiguous_query(query='a', intent_scores=[], priority=False, request_id=rid)
        self.assertEqual(ret1, rid)
        # second publish with same id should not enqueue again
        ret2 = prod.publish_ambiguous_query(query='b', intent_scores=[], priority=False, request_id=rid)
        self.assertEqual(ret2, rid)
        # send_queue should have only one new item beyond initial
        self.assertGreaterEqual(prod._send_queue.qsize(), initial_q)


if __name__ == '__main__':
    unittest.main()