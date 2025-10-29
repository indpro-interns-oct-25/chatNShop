from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RuleDecision:
    """Structured payload passed from rule-based engine to downstream services."""

    classification_status: str
    intent: Optional[Dict[str, Any]]
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    top_confidence: float = 0.0
    next_best_confidence: float = 0.0
    confidence_gap: float = 0.0
    needs_llm_review: bool = False
    trigger_reason: Optional[str] = None
    resolved_intent: Optional[str] = None
    resolved_action_code: Optional[str] = None
    is_fallback: bool = False
    config_variant: str = "default"
    rule_latency_ms: float = 0.0
    handoff_metadata: Dict[str, Any] = field(
        default_factory=lambda: {"triggered": False, "reason": None}
    )
    context_snippets: List[str] = field(default_factory=list)
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        """Serialize the dataclass into a dictionary for external consumers."""
        payload: Dict[str, Any] = {
            "classification_status": self.classification_status,
            "intent": dict(self.intent) if self.intent else None,
            "candidates": [dict(candidate) for candidate in self.candidates],
            "top_confidence": round(self.top_confidence, 4),
            "next_best_confidence": round(self.next_best_confidence, 4),
            "confidence_gap": round(self.confidence_gap, 4),
            "needs_llm_review": self.needs_llm_review,
            "trigger_reason": self.trigger_reason,
            "resolved_intent": self.resolved_intent,
            "resolved_action_code": self.resolved_action_code,
            "is_fallback": self.is_fallback,
            "config_variant": self.config_variant,
            "handoff_metadata": dict(self.handoff_metadata),
            "context_snippets": list(self.context_snippets),
            "rule_latency_ms": round(self.rule_latency_ms, 2),
        }

        if self.extra_metadata:
            payload.setdefault("extra_metadata", {}).update(self.extra_metadata)

        return payload


__all__ = ["RuleDecision"]
