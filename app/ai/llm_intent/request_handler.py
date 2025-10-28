"""Coordinator that applies trigger logic, invokes the LLM, and normalizes output."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.schemas.llm_intent import LLMIntentRequest

from .confidence_calibrator import TriggerContext, should_trigger_llm
from .entity_extractor import INTENT_CATEGORIES
from .fallback_manager import build_fallback_response
from .openai_client import OpenAIClient
from .response_parser import LLMIntentResponse as ParsedLLMResponse, parse_llm_response


class RequestHandler:
    """Execute the hybrid rule-based + LLM intent classification flow."""

    def __init__(self, client: Optional[OpenAIClient] = None) -> None:
        self.client = client

    def handle(self, payload: LLMIntentRequest) -> Dict[str, Any]:
        """Process an intent request and return a normalized response payload."""

        ctx = TriggerContext(
            top_confidence=payload.top_confidence,
            next_best_confidence=payload.next_best_confidence,
            action_code=payload.action_code,
            is_fallback=payload.is_fallback,
        )
        trigger, reason = should_trigger_llm(ctx)

        metadata = {
            "trigger_reason": reason,
            "rule_intent": payload.rule_intent,
            "rule_action_code": payload.action_code,
        }

        if not trigger:
            # Rule-based result is sufficiently confident; return passthrough.
            return {
                "triggered": False,
                "intent": payload.rule_intent or "unknown_intent",
                "intent_category": self._infer_category(payload.action_code),
                "action_code": payload.action_code or "UNKNOWN_INTENT",
                "confidence": payload.top_confidence,
                "requires_clarification": False,
                "clarification_message": None,
                "metadata": metadata,
            }

        try:
            raw_result = self._invoke_llm(payload)
            parsed: ParsedLLMResponse = parse_llm_response(raw_result)
            return {
                "triggered": True,
                "intent": parsed.intent,
                "intent_category": parsed.intent_category,
                "action_code": parsed.action_code,
                "confidence": parsed.confidence,
                "requires_clarification": False,
                "clarification_message": None,
                "metadata": {
                    **metadata,
                    "source": "llm",
                    "processing_time_ms": parsed.processing_time_ms,
                    "reasoning": parsed.reasoning,
                },
            }
        except Exception as exc:  # pragma: no cover - defensive safeguard
            fallback = build_fallback_response(reason="llm_failure")
            fallback_metadata = fallback.get("metadata", {})
            fallback_metadata.update({"error": str(exc), **metadata})
            fallback["metadata"] = fallback_metadata
            return {"triggered": True, **fallback}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _invoke_llm(self, payload: LLMIntentRequest) -> Dict[str, Any]:
        """Call the configured LLM client or fall back to simulation."""

        if self.client is None:
            return self._simulate_llm_response(payload)

        request_body = {
            "model": self.client.model_name,
            "timeout_ms": self.client.timeout_ms,
            "user_input": payload.user_input,
            "context": payload.context_snippets,
            "metadata": payload.metadata,
        }
        return self.client.complete(request_body)

    def _simulate_llm_response(self, payload: LLMIntentRequest) -> Dict[str, Any]:
        """Generate a deterministic stand-in response when no LLM is wired up."""

        action_code = payload.action_code or "HELP_GENERAL"
        intent_category = self._infer_category(action_code)
        intent_name = payload.rule_intent or f"llm_{action_code.lower()}"
        confidence = max(payload.top_confidence, 0.75)

        return {
            "intent": intent_name,
            "intent_category": intent_category,
            "action_code": action_code,
            "confidence": confidence,
            "reasoning": "Simulated LLM output (no API client configured)",
        }

    @staticmethod
    def _infer_category(action_code: Optional[str]) -> str:
        """Best-effort lookup of the category for a given action code."""

        if not action_code:
            return "SUPPORT_HELP"

        for category, codes in INTENT_CATEGORIES.items():
            if action_code in codes:
                return category
        return "SUPPORT_HELP"


__all__ = ["RequestHandler"]
