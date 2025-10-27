"""Thin OpenAI API client wrapper for LLM intent classification."""

from __future__ import annotations

from typing import Any, Dict

TARGET_P95_LATENCY_MS: int = 2000
"""LLM requests must complete within two seconds at the 95th percentile."""

MAX_REQUEST_COST_USD: float = 0.02
"""Per-call budget guardrail to keep usage within monthly allocations."""


class OpenAIClient:
    """Wrapper around the OpenAI SDK to support dependency injection in tests."""

    def __init__(self, api_key: str, model_name: str, timeout_ms: int = TARGET_P95_LATENCY_MS) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_ms = timeout_ms

    def complete(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a completion request to the OpenAI API.

        Implementations should enforce the ``timeout_ms`` for SLA compliance and
        monitor token usage to ensure each request remains below
        ``MAX_REQUEST_COST_USD``. Hook into the monitoring subsystem to emit
        latency and cost metrics for dashboards and alerting.
        """
        raise NotImplementedError("OpenAI API integration not implemented yet")


__all__ = ["TARGET_P95_LATENCY_MS", "MAX_REQUEST_COST_USD", "OpenAIClient"]
