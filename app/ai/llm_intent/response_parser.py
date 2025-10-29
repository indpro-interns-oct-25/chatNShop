"""Utilities for validating and normalizing responses from the LLM."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMIntentResponse:
    """Structured representation of the LLM output."""

    intent: str
    intent_category: str
    action_code: str
    confidence: float
    processing_time_ms: Optional[float] = None
    reasoning: Optional[str] = None


EXPECTED_SCHEMA: Dict[str, str] = {
    "intent": "Slug-like name of the identified intent",
    "intent_category": "One of the categories defined in INTENT_CATEGORIES",
    "action_code": "One of the ActionCode values consumed downstream",
    "confidence": "Float between 0.0 and 1.0",
    "processing_time_ms": "Optional runtime metric reported by the LLM",
    "reasoning": "Optional short justification string for audit trails",
}
"""Documentation of the properties expected from the LLM classifier."""


def parse_llm_response(raw: Dict[str, Any]) -> LLMIntentResponse:
    """Validate the raw LLM payload returned from GPT-4 models.

    The newer chat completions API returns a nested structure. This helper looks for a
    JSON object inside the assistant message content and performs schema validation
    before returning a normalized dataclass instance.
    """

    try:
        choice = raw["choices"][0]
        message = choice["message"]
        content = message.get("content")
    except (KeyError, IndexError, TypeError) as exc:  # pragma: no cover - defensive
        raise ValueError("Malformed OpenAI chat completion response") from exc

    if not content:
        raise ValueError("OpenAI response missing assistant content")

    if isinstance(content, list):
        content = "".join(part.get("text", "") for part in content)

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Assistant content is not valid JSON") from exc

    for required_key in ("intent", "intent_category", "action_code", "confidence"):
        if required_key not in payload:
            raise ValueError(f"LLM payload missing required key '{required_key}'")

    try:
        confidence = float(payload["confidence"])
    except (TypeError, ValueError):
        raise ValueError("Confidence must be a numeric value")

    confidence = max(0.0, min(confidence, 1.0))

    return LLMIntentResponse(
        intent=str(payload["intent"]),
        intent_category=str(payload["intent_category"]),
        action_code=str(payload["action_code"]),
        confidence=confidence,
        processing_time_ms=payload.get("processing_time_ms"),
        reasoning=payload.get("reasoning"),
    )


__all__ = ["LLMIntentResponse", "EXPECTED_SCHEMA", "parse_llm_response"]
