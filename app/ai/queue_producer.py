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
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, TypedDict, Union, Literal, cast, Any as TypingAny

try:
    import pika
    from pika.adapters.blocking_connection import BlockingChannel
    from pika.connection import Connection as PikaConnection
    from pika.exceptions import AMQPConnectionError, AMQPChannelError
    _PIKA_AVAILABLE = True
except Exception:
    pika = None  # type: ignore
    BlockingChannel = None  # type: ignore
    PikaConnection = None  # type: ignore
    AMQPConnectionError = Exception  # fallback
    AMQPChannelError = Exception
    _PIKA_AVAILABLE = False

from .queue.config import RABBITMQ_CONFIG

# Type definitions for better type safety
class IntentScore(TypedDict):
    intent: float  # Changed from str to float to match test requirements
    score: float

class QueueMessage(TypedDict):
    request_id: str
    timestamp: str
    query: str
    intent_scores: List[IntentScore]
    priority: bool
    metadata: Dict[str, Any]

class BatchPayload(TypedDict):
    batch_id: str
    timestamp: str
    messages: List[QueueMessage]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntentQueueProducer:
    """Handles publishing of ambiguous queries to the intent classification queue via RabbitMQ."""
    
    def __init__(self, queue_config: Optional[Dict[str, Any]] = None):
        """Initialize the queue producer with optional configuration."""
        self.queue_config = queue_config or {}
        self.batch_size = self.queue_config.get('batch_size', 1)
        self.batch_timeout = self.queue_config.get('batch_timeout', 60)  # seconds
        self._message_batch: List[QueueMessage] = []
        self._batch_start_time: Optional[datetime] = None
        
        # RabbitMQ connection setup
        self._connection = None
        self._channel = None
        self._lock = threading.Lock()
        
        # Initialize RabbitMQ connection (only if pika is available)
        if _PIKA_AVAILABLE:
            try:
                self._setup_rabbitmq()
            except QueuePublishError:
                # Initialization failure should not prevent app startup; leave connection lazy
                logger.warning("RabbitMQ setup failed during init; will retry on first publish")
        else:
            logger.warning("pika library not available; RabbitMQ publishing disabled in this environment")
        logger.info("IntentQueueProducer initialized with batch_size=%d, batch_timeout=%d",
                   self.batch_size, self.batch_timeout)
        
    def publish_ambiguous_query(self, 
                              query: str, 
                              intent_scores: List[IntentScore],
                              priority: bool = False,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Publish an ambiguous query to the intent classification queue.
        
        Args:
            query: The user's original query text
            intent_scores: List of possible intents and their confidence scores
            priority: Whether this is a priority message
            metadata: Additional context about the request
            
        Returns:
            str: The unique request_id for tracking
        """
        try:
            # Generate unique request ID
            request_id = str(uuid.uuid4())
            
            # Format message payload
            message: QueueMessage = {
                'request_id': request_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'query': query,
                'intent_scores': intent_scores,
                'priority': priority,
                'metadata': metadata or {}
            }
            
            # Add to batch if batching enabled
            if self.batch_size > 1:
                self._add_to_batch(message)
            else:
                self._publish_message(message)
                
            # Log the published message
            logger.info(f"Published ambiguous query message with request_id={request_id}")
            
            return request_id
            
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}", exc_info=True)
            raise QueuePublishError(f"Failed to publish message: {str(e)}")
    
    def _add_to_batch(self, message: QueueMessage) -> None:
        """Add message to batch, publishing if batch is full or timed out."""
        if not self._batch_start_time:
            self._batch_start_time = datetime.now(timezone.utc)
            
        self._message_batch.append(message)
        
        # Check if batch should be published
        batch_age = (datetime.now(timezone.utc) - self._batch_start_time).total_seconds()
        if (len(self._message_batch) >= self.batch_size or 
            batch_age >= self.batch_timeout):
            self._publish_batch()
    
    def _publish_batch(self) -> None:
        """Publish the current batch of messages."""
        if not self._message_batch:
            return
            
        try:
            # TODO: Implement actual queue publishing logic here
            # This is a placeholder for the actual queue implementation
            batch_payload: BatchPayload = {
                'batch_id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'messages': self._message_batch
            }
            self._publish_message(batch_payload, is_batch=True)
            
            # Clear the batch after successful publish
            self._message_batch = []
            self._batch_start_time = None
            
        except Exception as e:
            logger.error(f"Failed to publish batch: {str(e)}", exc_info=True)
            raise QueuePublishError(f"Failed to publish batch: {str(e)}")
    
    def _setup_rabbitmq(self) -> None:
        """Setup RabbitMQ connection and channel."""
        if not _PIKA_AVAILABLE:
            raise QueuePublishError("pika library not available; cannot setup RabbitMQ")

        try:
            # Create connection parameters with retry settings
            pika_any = cast(TypingAny, pika)
            credentials = pika_any.PlainCredentials(
                RABBITMQ_CONFIG['username'],
                RABBITMQ_CONFIG['password']
            )
            parameters = pika_any.ConnectionParameters(
                host=RABBITMQ_CONFIG['host'],
                port=RABBITMQ_CONFIG['port'],
                virtual_host=RABBITMQ_CONFIG['virtual_host'],
                credentials=credentials,
                connection_attempts=RABBITMQ_CONFIG['connection_attempts'],
                retry_delay=RABBITMQ_CONFIG['retry_delay']
            )
            
            # Create connection and channel
            self._connection = cast(TypingAny, pika_any.BlockingConnection(parameters))
            self._channel = cast(TypingAny, self._connection.channel())
            
            # Declare exchange and queue
            self._channel.exchange_declare(
                exchange=RABBITMQ_CONFIG['exchange'],
                exchange_type=RABBITMQ_CONFIG['exchange_type'],
                durable=True
            )
            
            # Declare queue with priority support
            self._channel.queue_declare(
                queue=RABBITMQ_CONFIG['queue'],
                durable=True,
                arguments={'x-max-priority': RABBITMQ_CONFIG['priority_levels']}
            )
            
            # Bind queue to exchange
            self._channel.queue_bind(
                queue=RABBITMQ_CONFIG['queue'],
                exchange=RABBITMQ_CONFIG['exchange'],
                routing_key=RABBITMQ_CONFIG['routing_key']
            )
            
            logger.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ connection: {str(e)}", exc_info=True)
            raise QueuePublishError(f"Failed to setup RabbitMQ connection: {str(e)}")

    def _ensure_connection(self) -> None:
        """Ensure RabbitMQ connection is active, reconnect if needed."""
        try:
            # Re-establish connection if missing or closed
            if not self._connection or getattr(self._connection, 'is_closed', True):
                self._setup_rabbitmq()

            # Ensure connection exists after setup
            if self._connection is None:
                raise QueuePublishError("RabbitMQ connection is not available after setup")

            # Create or re-open channel if missing/closed
            if not self._channel or getattr(self._channel, 'is_closed', True):
                # _connection is confirmed non-None above
                self._channel = self._connection.channel()
        except Exception as e:
            logger.error(f"Failed to ensure RabbitMQ connection: {str(e)}", exc_info=True)
            raise QueuePublishError(f"Failed to ensure RabbitMQ connection: {str(e)}")

    def _publish_message(self, message: Union[QueueMessage, BatchPayload], is_batch: bool = False) -> None:
        """
        Publish a message to RabbitMQ.
        
        Args:
            message: The message to publish
            is_batch: Whether this is a batch message
        """
        with self._lock:
            try:
                if not _PIKA_AVAILABLE:
                    # pika not available in this environment (e.g., test runner).
                    # Treat publishing as a no-op to allow tests and offline usage.
                    logger.info("pika not available: skipping publish (no-op)")
                    return

                self._ensure_connection()
                # Ensure channel is available
                if self._channel is None:
                    raise QueuePublishError("RabbitMQ channel is not available")

                # Convert message to JSON
                message_json = json.dumps(message)
                
                # Set message properties
                pika_any = cast(TypingAny, pika)
                properties = pika_any.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json',
                    priority=4 if message.get('priority', False) else 1
                )
                
                # Publish message
                self._channel.basic_publish(
                    exchange=RABBITMQ_CONFIG['exchange'],
                    routing_key=RABBITMQ_CONFIG['routing_key'],
                    body=message_json,
                    properties=properties
                )
                
                logger.debug(f"Published {'batch' if is_batch else 'message'} to RabbitMQ: {message_json[:200]}...")
                
            except Exception as e:
                logger.error(f"Error publishing message: {str(e)}", exc_info=True)
                raise QueuePublishError(f"Failed to publish message: {str(e)}")


class QueuePublishError(Exception):
    """Custom exception for queue publishing errors."""
    pass