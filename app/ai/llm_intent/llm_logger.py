from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional


_logger = logging.getLogger("app.llm_intent")


def _safe_payload(payload: Optional[Dict[str, Any]]) -> str:
    if not payload:
        return "{}"
    try:
        return json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(payload)


def log_request(
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    attempt: int,
    stream: bool,
    preview: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    _logger.info(
        "OpenAI request dispatched",
        extra={
            "event": "openai_request",
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "attempt": attempt,
            "stream": stream,
            "preview": preview,
            "metadata": _safe_payload(metadata),
        },
    )


def log_success(
    *,
    model: str,
    latency_ms: float,
    finish_reason: Optional[str],
    stream: bool,
    response_payload: Dict[str, Any],
) -> None:
    _logger.info(
        "OpenAI request succeeded",
        extra={
            "event": "openai_success",
            "model": model,
            "latency_ms": round(latency_ms, 2),
            "finish_reason": finish_reason,
            "stream": stream,
            "response": _safe_payload(response_payload),
        },
    )


def log_failure(
    *,
    model: str,
    attempt: int,
    error: Exception,
    code: str,
    will_retry: bool,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    _logger.warning(
        "OpenAI request failed",
        extra={
            "event": "openai_failure",
            "model": model,
            "attempt": attempt,
            "code": code,
            "will_retry": will_retry,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "metadata": _safe_payload(metadata),
        },
    )


def log_circuit_open(*, failure_count: int, reset_seconds: float) -> None:
    _logger.error(
        "OpenAI circuit breaker opened",
        extra={
            "event": "openai_circuit_open",
            "failure_count": failure_count,
            "reset_seconds": reset_seconds,
        },
    )


__all__ = ["log_request", "log_success", "log_failure", "log_circuit_open"]
