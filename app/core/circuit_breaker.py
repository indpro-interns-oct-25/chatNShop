"""Generic circuit breaker utility used to guard external dependencies."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional


class CircuitBreakerOpenError(RuntimeError):
    """Raised when outbound calls are blocked while the breaker is open."""


@dataclass
class CircuitBreakerState:
    state: str = "closed"
    failure_count: int = 0
    opened_at: Optional[float] = None


class CircuitBreaker:
    """Small circuit breaker implementation with half-open transition."""

    def __init__(self, *, failure_threshold: int, reset_timeout: float) -> None:
        if failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive")
        if reset_timeout <= 0:
            raise ValueError("reset_timeout must be positive")

        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._state = CircuitBreakerState()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def allow_request(self) -> bool:
        """Return True when the downstream call should proceed."""

        if self._state.state != "open":
            return True

        assert self._state.opened_at is not None
        if time.time() - self._state.opened_at >= self.reset_timeout:
            self._state.state = "half_open"
            return True
        return False

    def record_success(self) -> None:
        """Reset breaker statistics on successful call."""

        self._state = CircuitBreakerState()

    def record_failure(self) -> None:
        """Increment failure count and open the breaker when threshold reached."""

        self._state.failure_count += 1
        if self._state.failure_count >= self.failure_threshold:
            self._state.state = "open"
            self._state.opened_at = time.time()

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    @property
    def failure_count(self) -> int:
        return self._state.failure_count

    @property
    def state(self) -> str:
        return self._state.state

    @property
    def opened_at(self) -> Optional[float]:
        return self._state.opened_at


__all__ = ["CircuitBreaker", "CircuitBreakerOpenError"]
