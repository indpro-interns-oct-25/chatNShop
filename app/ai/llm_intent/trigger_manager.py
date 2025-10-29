"""Manage LLM fallback execution with retries, timeouts, and circuit breaking."""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, Optional

from app.ai.llm_intent.openai_client import OpenAIClient, CircuitBreakerOpenError
from app.ai.llm_intent.request_handler import RequestHandler
from app.core.circuit_breaker import CircuitBreaker
from app.monitoring.metrics import log_latency
from app.schemas.llm_intent import LLMIntentRequest
from app.utils.retry_logic import RetryExceededError, retry_operation


_logger = logging.getLogger("app.ai.llm_intent.trigger_manager")

_EXECUTOR = ThreadPoolExecutor(
    max_workers=int(os.getenv("LLM_TRIGGER_MAX_WORKERS", "4")),
    thread_name_prefix="llm-trigger",
)


def _build_handler() -> RequestHandler:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        _logger.warning("OPENAI_API_KEY not configured; using simulated LLM responses")
        return RequestHandler()

    try:
        client = OpenAIClient(api_key=api_key)
        return RequestHandler(client)
    except Exception as exc:  # pragma: no cover - defensive
        _logger.exception("Failed to initialize OpenAI client: %s", exc)
        return RequestHandler()


class LLMTriggerManager:
    """Coordinator that safely invokes the LLM fallback."""

    def __init__(
        self,
        handler: Optional[RequestHandler] = None,
        *,
        timeout_seconds: float = float(os.getenv("LLM_TRIGGER_TIMEOUT_SECONDS", "2.5")),
        max_retries: int = int(os.getenv("LLM_TRIGGER_MAX_RETRIES", "1")),
        circuit_failure_threshold: int = int(os.getenv("LLM_TRIGGER_FAILURE_THRESHOLD", "3")),
        circuit_reset_seconds: float = float(os.getenv("LLM_TRIGGER_RESET_SECONDS", "60")),
    ) -> None:
        self.handler = handler or _build_handler()
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=circuit_failure_threshold,
            reset_timeout=circuit_reset_seconds,
        )

    def invoke(self, request: LLMIntentRequest, *, metric_tags: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the LLM handler with resiliency guards."""

        start = time.perf_counter()
        tags = metric_tags or {}

        def _operation() -> Dict[str, Any]:
            if not self.circuit_breaker.allow_request():
                raise CircuitBreakerOpenError("LLM trigger circuit breaker is open")

            try:
                result = self._call_with_timeout(request)
            except Exception:
                self.circuit_breaker.record_failure()
                raise
            else:
                self.circuit_breaker.record_success()
                return result

        try:
            response = retry_operation(
                _operation,
                retries=self.max_retries,
                exceptions=(TimeoutError, CircuitBreakerOpenError),
                delay=0.2,
                backoff=2.0,
                jitter=0.25,
            )
        except CircuitBreakerOpenError:
            _logger.warning("LLM trigger suppressed due to open circuit", extra={"tags": tags})
            raise
        except RetryExceededError:
            _logger.error("LLM trigger retries exhausted", extra={"tags": tags})
            raise
        except TimeoutError:
            _logger.error("LLM trigger timed out", extra={"tags": tags})
            raise
        except Exception:
            _logger.exception("LLM trigger failed", extra={"tags": tags})
            raise

        log_latency("llm_trigger_latency_ms", start_time=start, tags=tags)
        return response

    def _call_with_timeout(self, request: LLMIntentRequest) -> Dict[str, Any]:
        future = _EXECUTOR.submit(self.handler.handle, request)
        try:
            return future.result(timeout=self.timeout_seconds)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise TimeoutError("LLM trigger exceeded timeout") from exc


__all__ = ["LLMTriggerManager"]
