"""
Queue producer for handling ambiguous queries from rule-based classification.

This module is responsible for:
1. Accepting ambiguous results from rule-based keyword matching
2. Generating unique request IDs for tracking
3. Publishing messages to the intent classification queue via RabbitMQ
4. Error handling and logging
"""

import json
import uuid
import logging
import threading
import queue as _queue
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, TypedDict, Union, cast

# -----------------------
# Optional external libs
# -----------------------
try:
    import pika
    from pika.adapters.blocking_connection import BlockingChannel  # type: ignore
    from pika.connection import Connection as PikaConnection  # type: ignore
    from pika.exceptions import AMQPConnectionError, AMQPChannelError  # type: ignore
    _PIKA_AVAILABLE = True
except Exception:
    pika = None  # type: ignore
    BlockingChannel = None  # type: ignore
    PikaConnection = None  # type: ignore
    AMQPConnectionError = Exception  # fallback
    AMQPChannelError = Exception
    _PIKA_AVAILABLE = False

# RabbitMQ config import — adjust path if your project layout differs
from .queue.config import RABBITMQ_CONFIG

# protobuf optional
try:
    from google.protobuf import struct_pb2
    from google.protobuf import json_format
    _PROTOBUF_AVAILABLE = True
except Exception:
    struct_pb2 = None  # type: ignore
    json_format = None  # type: ignore
    _PROTOBUF_AVAILABLE = False

# Attempt to import generated protos (optional)
try:
    from app.ai.protos import intent_message_pb2 as intent_message_pb2  # type: ignore
    _GENERATED_PROTO_AVAILABLE = True
except Exception:
    intent_message_pb2 = None  # type: ignore
    _GENERATED_PROTO_AVAILABLE = False

# -----------------------
# Type definitions
# -----------------------
class IntentScore(TypedDict):
    intent: str
    score: float


class RuleBasedResult(TypedDict, total=False):
    action_code: str
    confidence: float
    matched_keywords: List[str]


# Make metadata and conversation_history required so we can safely access them
class QueueMessage(TypedDict):
    request_id: str
    user_query: str
    session_id: Optional[str]
    user_id: Optional[str]
    conversation_history: List[Dict[str, Any]]
    rule_based_result: Optional[RuleBasedResult]
    timestamp: str
    priority: str  # 'normal' | 'high'
    metadata: Dict[str, Any]


class BatchPayload(TypedDict):
    batch_id: str
    timestamp: str
    messages: List[QueueMessage]


# -----------------------
# Logging
# -----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# -----------------------
# Custom exception
# -----------------------
class QueuePublishError(Exception):
    """Custom exception for queue publishing errors."""


# -----------------------
# Producer class
# -----------------------
class IntentQueueProducer:
    """Handles publishing of ambiguous queries to the intent classification queue via RabbitMQ."""

    def __init__(self, queue_config: Optional[Dict[str, Any]] = None):
        self.queue_config = queue_config or {}
        self.batch_size = int(self.queue_config.get("batch_size", 1))
        self.batch_timeout = float(self.queue_config.get("batch_timeout", 60.0))  # seconds
        self.serialization = str(self.queue_config.get("serialization", "json"))
        self._message_batch: List[QueueMessage] = []
        self._batch_start_time: Optional[datetime] = None

        # RabbitMQ connection fields
        self._connection = None
        self._channel = None
        self._lock = threading.Lock()

        # Background send queue and worker
        self._send_queue: _queue.Queue = _queue.Queue()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)

        # idempotency store
        self.enable_idempotency = bool(self.queue_config.get("enable_idempotency", False))
        self.idempotency_ttl = int(self.queue_config.get("idempotency_ttl", 300))
        self._idempotency_store: Dict[str, float] = {}
        self._idempotency_lock = threading.Lock()

        # Start worker thread
        self._worker_thread.start()

        # Try to set up RabbitMQ (non-fatal if it fails; will be retried on publish)
        if _PIKA_AVAILABLE:
            try:
                self._setup_rabbitmq()
            except Exception as exc:
                logger.warning("RabbitMQ setup failed during init; will retry on publish: %s", exc)
        else:
            logger.warning("pika library not available; RabbitMQ publishing disabled in this environment")

        logger.info(
            "IntentQueueProducer initialized with batch_size=%d, batch_timeout=%.1f",
            self.batch_size,
            self.batch_timeout,
        )

    from typing import List, Dict, Any, Optional, Union, cast

    def publish_ambiguous_query(
        self,
        query: str,
        intent_scores: List[IntentScore],
        priority: Union[bool, str] = False,
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        rule_based_result: Optional[RuleBasedResult] = None,
        serialization: Optional[str] = None,
        request_id: Optional[str] = None,
        wait_for_publish: bool = False,
    ) -> str:
        """
        Publish an ambiguous query to the intent classification queue.

        Returns:
            str: The unique request_id for tracking
        """
        request_id = request_id or str(uuid.uuid4())

        # Idempotency reservation (unchanged)
        if self.enable_idempotency:
            now_ts = datetime.now(timezone.utc).timestamp()
            with self._idempotency_lock:
                expired = [k for k, v in self._idempotency_store.items() if v < now_ts]
                for k in expired:
                    del self._idempotency_store[k]
                if request_id in self._idempotency_store:
                    logger.info("Duplicate request_id %s detected; skipping enqueue", request_id)
                    return request_id
                self._idempotency_store[request_id] = now_ts + self.idempotency_ttl

        # Priority normalization
        if isinstance(priority, bool):
            priority_str = "high" if priority else "normal"
        else:
            priority_str = str(priority)

        # Serialization
        serialization = serialization or self.serialization or "json"

        # Normalize metadata and optional fields
        metadata = dict(metadata or {})

        # prefer explicit pops from metadata if not provided directly
        session_id = session_id or metadata.pop("session_id", None)
        user_id = user_id or metadata.pop("user_id", None)

        # IMPORTANT: narrow conversation_history to a non-None list for Pylance
        # metadata.pop(...) could be None, so we explicitly coerce to an empty list if falsy
        conv_from_meta = metadata.pop("conversation_history", None)
        conversation_history_list: List[Dict[str, Any]] = cast(
            List[Dict[str, Any]],
            conversation_history or conv_from_meta or []
        )

        # Similarly ensure rule_based_result has correct shape (it's optional in TypedDict)
        rb_result: Optional[RuleBasedResult] = rule_based_result or metadata.pop("rule_based_result", None)

        # Build message (now conversation_history_list has concrete List[...] type)
        message: QueueMessage = {
            "request_id": request_id,
            "user_query": query,
            "session_id": session_id,
            "user_id": user_id,
            "conversation_history": conversation_history_list,
            "rule_based_result": rb_result,
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z",
            "priority": priority_str,
            "metadata": metadata or {},
        }

        # Attach detected intents under metadata safely
        message.setdefault("metadata", {})["intent_scores"] = intent_scores

        # Synchronous publish if requested
        if wait_for_publish:
            try:
                self._publish_message(message)
            except Exception as exc:
                if self.enable_idempotency:
                    with self._idempotency_lock:
                        self._idempotency_store.pop(request_id, None)
                raise QueuePublishError(str(exc)) from exc
        else:
            self._send_queue.put(message)

        logger.info("Enqueued ambiguous query message with request_id=%s", request_id)
        return request_id


    # -----------------------
    # Batching helpers
    # -----------------------
    def _add_to_batch(self, message: QueueMessage) -> None:
        if not self._batch_start_time:
            self._batch_start_time = datetime.now(timezone.utc)

        self._message_batch.append(message)

        batch_age = (datetime.now(timezone.utc) - self._batch_start_time).total_seconds()
        if len(self._message_batch) >= self.batch_size or batch_age >= self.batch_timeout:
            self._publish_batch()

    def _publish_batch(self) -> None:
        if not self._message_batch:
            return

        try:
            batch_payload: BatchPayload = {
                "batch_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z",
                "messages": self._message_batch,
            }
            self._publish_message(batch_payload, is_batch=True)
            self._message_batch = []
            self._batch_start_time = None
        except Exception as exc:
            logger.error("Failed to publish batch: %s", exc, exc_info=True)
            raise QueuePublishError(str(exc)) from exc

    # -----------------------
    # Background worker
    # -----------------------
    def _worker_loop(self) -> None:
        batch_messages: List[QueueMessage] = []
        batch_start: Optional[datetime] = None

        while not self._stop_event.is_set():
            try:
                msg = self._send_queue.get(timeout=1.0)
            except _queue.Empty:
                # timeout — flush batch if aged
                if batch_messages and batch_start:
                    age = (datetime.now(timezone.utc) - batch_start).total_seconds()
                    if age >= self.batch_timeout:
                        try:
                            self._message_batch = batch_messages.copy()
                            self._publish_batch()
                        except Exception:
                            logger.exception("Error publishing batch from worker")
                        finally:
                            batch_messages = []
                            batch_start = None
                continue
            except Exception:
                logger.exception("Unexpected error reading from send queue")
                continue

            # Received a message
            if self.batch_size > 1:
                if not batch_start:
                    batch_start = datetime.now(timezone.utc)
                batch_messages.append(cast(QueueMessage, msg))

                if len(batch_messages) >= self.batch_size:
                    try:
                        self._message_batch = batch_messages.copy()
                        self._publish_batch()
                    except Exception:
                        logger.exception("Error publishing batch from worker")
                    finally:
                        batch_messages = []
                        batch_start = None
            else:
                # immediate publish
                try:
                    self._publish_message(cast(QueueMessage, msg))
                except Exception:
                    logger.exception("Error publishing message from worker")

        # flush remaining on stop
        if batch_messages:
            try:
                self._message_batch = batch_messages.copy()
                self._publish_batch()
            except Exception:
                logger.exception("Error publishing final batch from worker")

    def stop(self, timeout: Optional[float] = None) -> None:
        """Stop the background worker (useful for tests/cleanup)."""
        self._stop_event.set()
        self._worker_thread.join(timeout=timeout)

    # -----------------------
    # RabbitMQ helpers
    # -----------------------
    def _setup_rabbitmq(self) -> None:
        """Setup RabbitMQ connection and channel (raises QueuePublishError on failure)."""
        if not _PIKA_AVAILABLE:
            raise QueuePublishError("pika library not available; cannot setup RabbitMQ")

        try:
            pika_any = cast(Any, pika)
            credentials = pika_any.PlainCredentials(
                RABBITMQ_CONFIG["username"], RABBITMQ_CONFIG["password"]
            )
            parameters = pika_any.ConnectionParameters(
                host=RABBITMQ_CONFIG["host"],
                port=RABBITMQ_CONFIG["port"],
                virtual_host=RABBITMQ_CONFIG.get("virtual_host", "/"),
                credentials=credentials,
                connection_attempts=RABBITMQ_CONFIG.get("connection_attempts", 3),
                retry_delay=RABBITMQ_CONFIG.get("retry_delay", 5),
            )

            self._connection = cast(Any, pika_any.BlockingConnection(parameters))
            self._channel = cast(Any, self._connection.channel())

            # Exchange / queue setup
            self._channel.exchange_declare(
                exchange=RABBITMQ_CONFIG["exchange"],
                exchange_type=RABBITMQ_CONFIG.get("exchange_type", "direct"),
                durable=True,
            )

            queue_args: Dict[str, Any] = {}
            if RABBITMQ_CONFIG.get("priority_levels"):
                queue_args["arguments"] = {"x-max-priority": int(RABBITMQ_CONFIG["priority_levels"])}

            self._channel.queue_declare(queue=RABBITMQ_CONFIG["queue"], durable=True, **queue_args)

            self._channel.queue_bind(
                queue=RABBITMQ_CONFIG["queue"],
                exchange=RABBITMQ_CONFIG["exchange"],
                routing_key=RABBITMQ_CONFIG.get("routing_key", ""),
            )

            logger.info("Successfully connected to RabbitMQ")
        except Exception as exc:
            logger.error("Failed to setup RabbitMQ connection: %s", exc, exc_info=True)
            raise QueuePublishError(str(exc)) from exc

    def _ensure_connection(self) -> None:
        """Ensure RabbitMQ connection and channel exist, reconnect if needed."""
        if not _PIKA_AVAILABLE:
            raise QueuePublishError("pika library not available; cannot ensure RabbitMQ connection")

        try:
            if not self._connection or getattr(self._connection, "is_closed", True):
                self._setup_rabbitmq()

            if self._connection is None:
                raise QueuePublishError("RabbitMQ connection unavailable after setup")

            if not self._channel or getattr(self._channel, "is_closed", True):
                self._channel = self._connection.channel()
        except Exception as exc:
            logger.error("Failed to ensure RabbitMQ connection: %s", exc, exc_info=True)
            raise QueuePublishError(str(exc)) from exc

    def _publish_message(self, message: Union[QueueMessage, BatchPayload], is_batch: bool = False) -> None:
        """
        Publish a message (or batch payload) to RabbitMQ.
        This function is thread-safe (uses a lock) and raises QueuePublishError on failures.
        """
        with self._lock:
            try:
                if not _PIKA_AVAILABLE:
                    logger.info("pika not available: skipping publish (no-op)")
                    return

                # Ensure connection/channel are ready
                self._ensure_connection()
                if self._channel is None:
                    raise QueuePublishError("RabbitMQ channel is not available")

                pika_any = cast(Any, pika)

                # Choose serialization: prefer self.serialization for batch as well
                used_serialization = self.serialization or "json"
                if is_batch and self.serialization:
                    used_serialization = self.serialization

                if used_serialization == "protobuf":
                    # ensure protobuf is available (narrow types for Pylance)
                    if not _PROTOBUF_AVAILABLE or struct_pb2 is None or json_format is None:
                        raise QueuePublishError("Protobuf serialization requested but protobuf package not available")
                    struct_module = cast(Any, struct_pb2)
                    json_fmt = cast(Any, json_format)

                    struct = struct_module.Struct()
                    # ParseDict requires a dict — message is a TypedDict (dict-like)
                    json_fmt.ParseDict(cast(dict, message), struct)
                    body = struct.SerializeToString()
                    content_type = "application/x-protobuf"
                else:
                    # JSON fallback
                    body = json.dumps(cast(dict, message), default=str)
                    content_type = "application/json"

                # Compute priority and correlation_id
                priority_val = 1
                correlation_id = None
                if isinstance(message, dict):
                    if not is_batch:
                        p = cast(dict, message).get("priority", "normal")
                        priority_val = 4 if p == "high" else 1
                        correlation_id = cast(dict, message).get("request_id")
                    else:
                        correlation_id = cast(dict, message).get("batch_id")

                properties = pika_any.BasicProperties(
                    delivery_mode=2,  # persistent
                    content_type=content_type,
                    priority=int(priority_val),
                    correlation_id=correlation_id,
                )

                # Publish using configured exchange/routing_key
                self._channel.basic_publish(
                    exchange=RABBITMQ_CONFIG["exchange"],
                    routing_key=RABBITMQ_CONFIG.get("routing_key", ""),
                    body=body,
                    properties=properties,
                )

                logger.debug(
                    "Published %s to RabbitMQ (serialization=%s)",
                    "batch" if is_batch else "message",
                    used_serialization,
                )

            except Exception as exc:
                logger.error("Error publishing message: %s", exc, exc_info=True)
                raise QueuePublishError(str(exc)) from exc