"""
User-friendly error formatting, escalation metadata, and UNCLEAR responses.
"""

from __future__ import annotations
from typing import Dict, List

def build_user_error_response(user_message: str, internal_error: str) -> Dict:
    """Return a friendly message payload for end-users while keeping internal context for logs."""
    return {
        "user_message": "Sorry — something went wrong while processing your request. Please try again in a moment.",
        "internal_error": internal_error,
        "suggestions": [
            "Try again in a few seconds",
            "Provide more details (product name, order number, or clear action)"
        ],
        "original_input": user_message
    }


def build_unclear_intent_response(suggested_questions: List[str]) -> Dict:
    """
    Return the canonical UNCLEAR response which the system should use when
    the model returns ambiguous/low-confidence answers.
    """
    return {
        "action_code": "UNCLEAR",
        "confidence": 0.0,
        "reasoning": "Ambiguous input — require user clarification",
        "clarifying_questions": suggested_questions
    }
