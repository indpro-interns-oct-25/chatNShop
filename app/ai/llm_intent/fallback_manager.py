"""Fallback logic used when the LLM cannot determine an intent."""

from __future__ import annotations

from typing import Dict

DEFAULT_FALLBACK_INTENT: str = "clarify_intent"
DEFAULT_FALLBACK_CATEGORY: str = "SUPPORT_HELP"
DEFAULT_FALLBACK_ACTION: str = "HELP_GENERAL"
DEFAULT_CLARIFICATION_MESSAGE: str = (
    "I'm not sure I understood that. Could you rephrase or provide more details?"
)


def build_fallback_response(reason: str) -> Dict[str, object]:
    """Return a standardized payload when both rule-based and LLM fail."""

    return {
        "intent": DEFAULT_FALLBACK_INTENT,
        "intent_category": DEFAULT_FALLBACK_CATEGORY,
        "action_code": DEFAULT_FALLBACK_ACTION,
        "confidence": 0.0,
        "requires_clarification": True,
        "clarification_message": DEFAULT_CLARIFICATION_MESSAGE,
        "metadata": {"fallback_reason": reason},
    }


__all__ = [
    "DEFAULT_FALLBACK_INTENT",
    "DEFAULT_FALLBACK_CATEGORY",
    "DEFAULT_FALLBACK_ACTION",
    "DEFAULT_CLARIFICATION_MESSAGE",
    "build_fallback_response",
]
