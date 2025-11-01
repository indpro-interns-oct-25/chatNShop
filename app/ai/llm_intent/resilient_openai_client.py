"""
Robust OpenAI client wrapper implementing:
- retries with exponential backoff
- classification of common errors (rate limit, timeout, 5xx)
- returns structured responses and error metadata
"""

from __future__ import annotations
import time
import logging
from typing import Any, Dict, Optional
import random

# If you have the official OpenAI library installed, import it here.
try:
    import openai
except Exception:
    openai = None

logger = logging.getLogger(__name__)


class LLMRequestError(Exception):
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


class ResilientOpenAIClient:
    def __init__(self, api_key: str, model_name: str = "gpt-4-turbo", max_retries: int = 3, base_backoff: float = 0.5):
        self.api_key = api_key
        self.model_name = model_name
        self.max_retries = max_retries
        self.base_backoff = base_backoff

        if openai:
            openai.api_key = api_key

    def complete(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform the LLM call with retry and backoff. Returns parsed dict on success,
        or raises LLMRequestError on final failure.
        """
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # adapt to your request shape; we assume request_body contains 'user_input' and 'context'
                # Use OpenAI chat completion if available
                if openai is None:
                    # running in mock/offline env — simulate deterministic response
                    response = {
                        "intent": "simulated_intent",
                        "intent_category": "SIMULATION",
                        "action_code": request_body.get("metadata", {}).get("action_code", "HELP_GENERAL"),
                        "confidence": 0.9,
                        "reasoning": "Simulated response (no openai package installed)",
                        "processing_time_ms": 50,
                    }
                    return response

                # Example using Chat Completions API (adjust to your installed client)
                completion = openai.ChatCompletion.create(
                    model=self.model_name,
                    messages=request_body.get("messages"),
                    max_tokens=request_body.get("max_tokens", 200),
                    temperature=request_body.get("temperature", 0.0),
                    timeout=request_body.get("timeout_s", 10),
                )
                # Extract assistant content — expecting JSON text
                content = completion["choices"][0]["message"]["content"]
                # try parse JSON safely at caller side; here return raw content container
                return {"raw_content": content, "usage": completion.get("usage")}
            except Exception as exc:
                last_exc = exc
                err_str = getattr(exc, "message", str(exc))
                # classify
                code = "unknown_error"
                if hasattr(exc, "http_status"):
                    if getattr(exc, "http_status") == 429:
                        code = "rate_limit"
                    elif 500 <= getattr(exc, "http_status") < 600:
                        code = "server_error"
                # Sleep with jittered exponential backoff
                jitter = random.uniform(0, 0.1 * attempt)
                backoff = self.base_backoff * (2 ** (attempt - 1)) + jitter
                logger.warning("LLM call failed (attempt %s/%s): %s; backoff=%.2fs", attempt, self.max_retries, err_str, backoff)
                time.sleep(backoff)
                # If last attempt, raise final error
        raise LLMRequestError("LLM request ultimately failed", code=getattr(last_exc, "code", None), details={"exception": str(last_exc)})
