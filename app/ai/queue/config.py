"""RabbitMQ configuration settings."""

import os
from typing import Dict, Any

RABBITMQ_CONFIG: Dict[str, Any] = {
    'host': os.getenv('RABBITMQ_HOST', 'localhost'),
    'port': int(os.getenv('RABBITMQ_PORT', '5672')),
    'username': os.getenv('RABBITMQ_USERNAME', 'guest'),
    'password': os.getenv('RABBITMQ_PASSWORD', 'guest'),
    'virtual_host': os.getenv('RABBITMQ_VHOST', '/'),
    'exchange': 'intent_classification',
    'exchange_type': 'direct',
    'queue': 'ambiguous_intents',
    'routing_key': 'ambiguous.intent',
    'priority_levels': 5,  # Number of priority levels (1-5)
    'connection_attempts': 3,
    'retry_delay': 5,  # seconds
}