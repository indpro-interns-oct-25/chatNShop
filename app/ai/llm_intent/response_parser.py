"""Utilities for validating and normalizing responses from the LLM."""

from __future__ import annotations

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
    """Validate the raw LLM payload and clamp confidence into [0, 1]."""

    try:
        intent = raw["intent"]
        intent_category = raw["intent_category"]
        action_code = raw["action_code"]
        confidence = float(raw["confidence"])
    except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ValueError("Malformed LLM intent response") from exc

    confidence = max(0.0, min(confidence, 1.0))

    return LLMIntentResponse(
        intent=intent,
        intent_category=intent_category,
        action_code=action_code,
        confidence=confidence,
        processing_time_ms=raw.get("processing_time_ms"),
        reasoning=raw.get("reasoning"),
    )


__all__ = ["LLMIntentResponse", "EXPECTED_SCHEMA", "parse_llm_response"]
