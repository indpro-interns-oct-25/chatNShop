"""Confidence calibration rules governing when the LLM should activate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Set


# ---------------------------------------------------------------------------
# Trigger configuration
# ---------------------------------------------------------------------------

LOW_CONFIDENCE_THRESHOLD: float = 0.50
"""Invoke LLM when rule-based confidence falls below this value."""

AMBIGUITY_DELTA: float = 0.10
"""Escalate if top-two rule-based scores differ by less than this delta."""

RULE_BASED_ESCALATION_CODES: Set[str] = {
    "UNKNOWN_INTENT",
    "PAYMENT_FAILED_HELP",
    "ORDER_CANCEL",
    "REPORT_FRAUD",
    "PERSONALIZED_RECOMMENDATIONS",
    "INITIATE_RETURN",
    "CONTACT_SUPPORT",
}
"""Action codes that always require LLM review due to high business risk."""


@dataclass(frozen=True)
class TriggerContext:
    """Snapshot of rule-based classifier metrics for escalation checks."""

    top_confidence: float
    next_best_confidence: float
    action_code: Optional[str]
    is_fallback: bool


def should_trigger_llm(ctx: TriggerContext) -> tuple[bool, str]:
    """Evaluate whether the LLM classifier must be activated.

    Returns a tuple of ``(should_trigger, reason)`` where ``reason`` captures the
    trigger that fired to support observability and downstream analytics.
    """

    if ctx.action_code in RULE_BASED_ESCALATION_CODES:
        return True, "escalation_action_code"

    if ctx.is_fallback:
        return True, "rule_based_fallback"

    if ctx.top_confidence < LOW_CONFIDENCE_THRESHOLD:
        return True, "low_confidence_threshold"

    if (ctx.top_confidence - ctx.next_best_confidence) < AMBIGUITY_DELTA:
        return True, "ambiguous_ranking"

    return False, "sufficient_confidence"


__all__ = [
    "LOW_CONFIDENCE_THRESHOLD",
    "AMBIGUITY_DELTA",
    "RULE_BASED_ESCALATION_CODES",
    "TriggerContext",
    "should_trigger_llm",
]
