"""Utility helpers for retrying transient operations."""

from __future__ import annotations

import random
import time
from typing import Callable, Iterable, Tuple, Type, TypeVar


_T = TypeVar("_T")


class RetryExceededError(RuntimeError):
    """Raised when retry attempts are exhausted without success."""


def retry_operation(
    operation: Callable[[], _T],
    *,
    retries: int = 3,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    delay: float = 0.25,
    backoff: float = 2.0,
    jitter: float = 0.1,
) -> _T:
    """Execute ``operation`` with simple exponential backoff.

    Args:
        operation: Zero-argument callable to execute.
        retries: Number of retry attempts to make after the first failure.
        exceptions: Exception types that should trigger a retry.
        delay: Initial delay (in seconds) before the first retry.
        backoff: Multiplier applied to the delay after each failure.
        jitter: Random jitter factor applied to avoid coordinated retries.

    Returns:
        The value returned by ``operation`` if successful.

    Raises:
        RetryExceededError: When the operation fails after all attempts.
        Exception: Re-raises the last exception encountered if it is not
            part of the ``exceptions`` tuple.
    """

    attempt = 0
    sleep = max(delay, 0.0)
    while True:
        try:
            return operation()
        except exceptions as exc:  # type: ignore[misc]
            if attempt >= retries:
                raise RetryExceededError("Operation exceeded retry attempts") from exc
            attempt += 1
            if sleep > 0:
                jitter_factor = 1 + random.uniform(-jitter, jitter) if jitter else 1.0
                time.sleep(sleep * jitter_factor)
                sleep *= backoff if backoff > 0 else 1.0
        except Exception:
            # Unexpected exception types should not trigger retries.
            raise


__all__ = ["retry_operation", "RetryExceededError"]
