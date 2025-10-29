"""
Fallback logic used when the LLM cannot determine an intent.
"""

from __future__ import annotations
from typing import Dict, List

# -------------------------------------------------------------------
# ✅ Default constants
# -------------------------------------------------------------------
DEFAULT_FALLBACK_INTENT: str = "clarify_intent"
DEFAULT_FALLBACK_CATEGORY: str = "SUPPORT_HELP"
DEFAULT_FALLBACK_ACTION: str = "HELP_GENERAL"
DEFAULT_CLARIFICATION_MESSAGE: str = (
    "I'm not sure I understood that. Could you rephrase or provide more details?"
)

# -------------------------------------------------------------------
# ✅ Primary fallback response
# -------------------------------------------------------------------
def build_fallback_response(reason: str) -> Dict[str, object]:
    """
    Return a standardized payload when both rule-based and LLM methods fail.
    This ensures the system never crashes on ambiguous or failed queries.
    """
    return {
        "intent": DEFAULT_FALLBACK_INTENT,
        "intent_category": DEFAULT_FALLBACK_CATEGORY,
        "action_code": DEFAULT_FALLBACK_ACTION,
        "confidence": 0.0,
        "requires_clarification": True,
        "clarification_message": DEFAULT_CLARIFICATION_MESSAGE,
        "metadata": {"fallback_reason": reason},
    }

# -------------------------------------------------------------------
# ✅ Optional "UNCLEAR" intent response (for low-confidence cases)
# -------------------------------------------------------------------
def build_unclear_response(suggested_questions: List[str]) -> Dict[str, object]:
    """
    Return an UNCLEAR response with suggested clarifying questions.
    Used when LLM confidence is low or multiple conflicting intents detected.
    """
    return {
        "intent": "unclear",
        "intent_category": DEFAULT_FALLBACK_CATEGORY,
        "action_code": "UNCLEAR",
        "confidence": 0.0,
        "requires_clarification": True,
        "clarification_message": DEFAULT_CLARIFICATION_MESSAGE,
        "clarifying_questions": suggested_questions,
        "metadata": {"fallback_reason": "unclear_intent"},
    }

# -------------------------------------------------------------------
# ✅ Public exports
# -------------------------------------------------------------------
__all__ = [
    "DEFAULT_FALLBACK_INTENT",
    "DEFAULT_FALLBACK_CATEGORY",
    "DEFAULT_FALLBACK_ACTION",
    "DEFAULT_CLARIFICATION_MESSAGE",
    "build_fallback_response",
    "build_unclear_response",
]
