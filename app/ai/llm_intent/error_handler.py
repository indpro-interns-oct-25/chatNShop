"""Centralized error handling helpers for the LLM intent pipeline."""

from __future__ import annotations

import logging
from typing import Any, Dict

from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

from .fallback_manager import build_fallback_response
from app.core.circuit_breaker import CircuitBreakerOpenError


logger = logging.getLogger("app.llm_intent.error_handler")


_REASON_MAP = {
    RateLimitError: "llm_rate_limited",
    APITimeoutError: "llm_timeout",
    APIConnectionError: "llm_connection_error",
    APIError: "llm_api_error",
}


def determine_reason(exc: Exception) -> str:
    """Return a stable fallback reason string for a given exception."""

    for error_type, reason in _REASON_MAP.items():
        if isinstance(exc, error_type):
            return reason
    if isinstance(exc, CircuitBreakerOpenError):
        return "llm_circuit_open"
    return "llm_failure"


def handle_llm_exception(exc: Exception, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Log and transform an exception into a standardized fallback payload."""

    reason = determine_reason(exc)

    log_message = "LLM invocation failed"
    if reason == "llm_circuit_open":
        logger.error("%s due to circuit breaker: %s", log_message, exc)
    elif reason == "llm_rate_limited":
        logger.warning("%s due to rate limiting: %s", log_message, exc)
    else:
        logger.exception("%s: %s", log_message, exc)

    fallback = build_fallback_response(reason=reason)
    fallback_metadata = fallback.get("metadata", {})
    fallback_metadata.update(
        {
            "error": str(exc),
            "error_type": type(exc).__name__,
            **(metadata or {}),
        }
    )
    fallback["metadata"] = fallback_metadata
    return fallback


__all__ = ["determine_reason", "handle_llm_exception"]
