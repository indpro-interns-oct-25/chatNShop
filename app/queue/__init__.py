"""
Queue Infrastructure Module (CNS-21)

Provides message queue infrastructure for asynchronous LLM intent classification.
Handles ambiguous queries from CNS-12 and routes them to LLM processing.
"""

from .queue_manager import QueueManager
from .config import QueueConfig

__all__ = ["QueueManager", "QueueConfig"]
