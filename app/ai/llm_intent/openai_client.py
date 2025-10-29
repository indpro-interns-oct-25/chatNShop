
from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Sequence

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, OpenAIError, RateLimitError

TARGET_P95_LATENCY_MS: int = 2000
"""LLM requests must complete within two seconds at the 95th percentile."""

MAX_REQUEST_COST_USD: float = 0.02
"""Per-call budget guardrail to keep usage within monthly allocations."""

DEFAULT_TEMPERATURE: float = 0.2
DEFAULT_MAX_TOKENS: int = 600
DEFAULT_TIMEOUT_SECONDS: float = 15.0
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_BACKOFF_FACTOR: float = 0.75
MAX_BACKOFF_SECONDS: float = 8.0


SYSTEM_PROMPT: str = (
    "You are an intent classification engine for an e-commerce support assistant. "
    "Return ONLY a compact JSON object with the keys: intent, intent_category, action_code, "
    "confidence, reasoning (optional), and processing_time_ms (optional). Confidence must be a "
    "float between 0 and 1. Use intent_category and action_code that best align with the user input. "
    "Do not include Markdown, explanations, or additional text outside the JSON object."
)


class OpenAIClient:
    """Wrapper around the OpenAI SDK to support dependency injection in tests."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        timeout_ms: int = TARGET_P95_LATENCY_MS,
        *,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        max_backoff_seconds: float = MAX_BACKOFF_SECONDS,
        logger: Optional[logging.Logger] = None,
        client: Optional[OpenAI] = None,
    ) -> None:
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_ms = timeout_ms
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_backoff_seconds = max_backoff_seconds
        self.logger = logger or logging.getLogger(__name__)
        self._client = client or OpenAI(api_key=api_key)
        self.timeout_seconds = max(timeout_ms / 1000, 0.1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def complete(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a completion request to the OpenAI API with retries and logging."""

        user_input = self._get_required(payload, "user_input")
        context_snippets = payload.get("context", [])
        metadata = payload.get("metadata", {})
        request_model = payload.get("model") or self.model_name
        temperature = float(payload.get("temperature", self.temperature))
        max_tokens = int(payload.get("max_tokens", self.max_tokens))

        attempt = 0
        while True:
            attempt += 1
            self.logger.info(
                "Dispatching OpenAI completion",
                extra={
                    "event": "openai_completion_request",
                    "model": request_model,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "attempt": attempt,
                    "context_size": len(context_snippets),
                    "user_input_preview": user_input[:120],
                },
            )

            try:
                messages = self._build_messages(user_input, context_snippets, metadata)
                start = time.perf_counter()
                response = self._client.chat.completions.create(
                    model=request_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout_seconds,
                )
                latency_ms = (time.perf_counter() - start) * 1000
                parsed = self._parse_response(response, latency_ms)
                self.logger.info(
                    "OpenAI completion successful",
                    extra={
                        "event": "openai_completion_success",
                        "model": request_model,
                        "latency_ms": round(latency_ms, 2),
                        "finish_reason": response.choices[0].finish_reason,
                    },
                )
                return parsed
            except RateLimitError as exc:
                self._log_exception(exc, attempt, request_model, will_retry=True, code="rate_limit")
                if not self._maybe_retry(attempt):
                    raise
            except (APITimeoutError, APIConnectionError) as exc:
                self._log_exception(exc, attempt, request_model, will_retry=True, code="transient")
                if not self._maybe_retry(attempt):
                    raise
            except APIStatusError as exc:
                # Retry 429/5xx responses; otherwise propagate immediately.
                should_retry = exc.status_code in {429, 500, 502, 503, 504}
                self._log_exception(
                    exc,
                    attempt,
                    request_model,
                    will_retry=should_retry,
                    code=f"status_{exc.status_code}",
                )
                if should_retry:
                    if not self._maybe_retry(attempt):
                        raise
                else:
                    raise
            except OpenAIError as exc:
                self._log_exception(exc, attempt, request_model, will_retry=False, code="openai_error")
                raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_messages(
        self,
        user_input: str,
        context_snippets: Sequence[str],
        metadata: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        context_section = (
            "\n".join(f"- {str(snippet)}" for snippet in context_snippets)
            if context_snippets
            else "None"
        )
        if metadata:
            try:
                metadata_section = json.dumps(metadata, ensure_ascii=False, indent=2)
            except TypeError:
                metadata_section = str(metadata)
        else:
            metadata_section = "None"

        user_prompt = (
            "User utterance:\n"
            f"{user_input}\n\n"
            "Context snippets (if any):\n"
            f"{context_section}\n\n"
            "Metadata (diagnostics):\n"
            f"{metadata_section}\n\n"
            "Respond strictly with JSON following the required schema."
        )

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    def _parse_response(self, response: Any, latency_ms: float) -> Dict[str, Any]:
        if not response.choices:
            raise ValueError("OpenAI response missing choices")

        message = response.choices[0].message
        content = (message.content or "").strip()
        data = self._extract_json(content)

        required_keys = {"intent", "intent_category", "action_code", "confidence"}
        missing = required_keys - data.keys()
        if missing:
            raise ValueError(f"LLM response missing required keys: {sorted(missing)}")

        if "processing_time_ms" not in data or data["processing_time_ms"] in (None, ""):
            data["processing_time_ms"] = round(latency_ms, 2)

        confidence = float(data["confidence"])
        data["confidence"] = max(0.0, min(confidence, 1.0))

        return {
            "intent": str(data["intent"]),
            "intent_category": str(data["intent_category"]),
            "action_code": str(data["action_code"]),
            "confidence": data["confidence"],
            "reasoning": data.get("reasoning"),
            "processing_time_ms": data.get("processing_time_ms"),
        }

    def _extract_json(self, content: str) -> Dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise ValueError("Unable to parse JSON from LLM response")

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ValueError("Malformed JSON emitted by LLM") from exc

    def _maybe_retry(self, attempt: int) -> bool:
        if attempt > self.max_retries:
            return False

        backoff_seconds = min(self.max_backoff_seconds, self.backoff_factor * (2 ** (attempt - 1)))
        time.sleep(backoff_seconds)
        return True

    def _log_exception(
        self,
        exc: Exception,
        attempt: int,
        model: str,
        *,
        will_retry: bool,
        code: str,
    ) -> None:
        self.logger.warning(
            "OpenAI completion failed",
            extra={
                "event": "openai_completion_error",
                "model": model,
                "attempt": attempt,
                "will_retry": will_retry,
                "code": code,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
        )

    @staticmethod
    def _get_required(payload: Dict[str, Any], key: str) -> Any:
        try:
            return payload[key]
        except KeyError as exc:  # pragma: no cover - defensive safeguard
            raise ValueError(f"'{key}' is required in payload") from exc


def build_openai_client_from_env(logger: Optional[logging.Logger] = None) -> Optional[OpenAIClient]:
    """Factory that wires up ``OpenAIClient`` using environment variables."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        if logger:
            logger.info("OPENAI_API_KEY not set – LLM intent requests will be simulated")
        return None

    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", DEFAULT_TEMPERATURE))
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", DEFAULT_MAX_TOKENS))
    timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
    max_retries = int(os.getenv("OPENAI_MAX_RETRIES", DEFAULT_MAX_RETRIES))
    backoff_factor = float(os.getenv("OPENAI_RETRY_BACKOFF_BASE", DEFAULT_BACKOFF_FACTOR))
    max_backoff_seconds = float(os.getenv("OPENAI_RETRY_BACKOFF_MAX", MAX_BACKOFF_SECONDS))

    timeout_ms = int(timeout_seconds * 1000)

    return OpenAIClient(
        api_key=api_key,
        model_name=model_name,
        timeout_ms=timeout_ms,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        max_backoff_seconds=max_backoff_seconds,
        logger=logger,
    )


__all__ = [
    "TARGET_P95_LATENCY_MS",
    "MAX_REQUEST_COST_USD",
    "OpenAIClient",
    "build_openai_client_from_env",
]
