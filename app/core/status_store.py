"""
Status Store - In-memory and Redis-based request status tracking.
"""

from datetime import datetime, timezone
from typing import Optional, Dict
from app.schemas.request_status import RequestStatus, ResultSchema


class InMemoryStatusStore:
    """
    Simple in-memory fallback for request status tracking.
    Used when Redis is unavailable or for testing.
    """

    def __init__(self):
        self._store: Dict[str, RequestStatus] = {}

    def save(self, status: RequestStatus):
        """Save or update a RequestStatus in memory."""
        self._store[status.request_id] = status

    def get(self, request_id: str) -> Optional[RequestStatus]:
        """Retrieve a RequestStatus by ID."""
        return self._store.get(request_id)

    def update_status(self, request_id: str, new_status: str):
        """Update the status of a request."""
        if request_id in self._store:
            entry = self._store[request_id]
            entry.status = new_status
            if new_status == "PROCESSING":
                entry.started_at = datetime.now(timezone.utc)
            elif new_status in ["COMPLETED", "FAILED"]:
                entry.completed_at = datetime.now(timezone.utc)
            self._store[request_id] = entry

    def complete_request(self, request_id: str, result: Optional[ResultSchema] = None):
        """Mark request as completed and store result."""
        if request_id in self._store:
            entry = self._store[request_id]
            entry.status = "COMPLETED"
            entry.completed_at = datetime.now(timezone.utc)
            entry.result = result
            self._store[request_id] = entry

    def clear(self):
        """Clear all entries (for testing)."""
        self._store.clear()
