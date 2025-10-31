"""Coordinator that applies trigger logic, invokes the LLM, and normalizes output."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.schemas.llm_intent import LLMIntentRequest

from .confidence_calibrator import TriggerContext, should_trigger_llm
from .entity_extractor import INTENT_CATEGORIES
from .fallback_manager import build_fallback_response
from .openai_client import OpenAIClient
from .response_parser import LLMIntentResponse as ParsedLLMResponse, parse_llm_response
from .prompt_loader import PromptLoader, PromptLoadError, get_prompt_loader
import logging

logger = logging.getLogger("request_handler")


class RequestHandler:
    """Execute the hybrid rule-based + LLM intent classification flow."""

    def __init__(
        self, 
        client: Optional[OpenAIClient] = None,
        prompt_loader: Optional[PromptLoader] = None
    ) -> None:
        """
        Initialize request handler.
        
        Args:
            client: OpenAI client instance (optional, will use default if None)
            prompt_loader: Prompt loader instance (optional, will use singleton if None)
        """
        self.client = client
        try:
            self.prompt_loader = prompt_loader or get_prompt_loader()
            logger.info("RequestHandler initialized with prompt loader")
        except PromptLoadError as e:
            logger.warning(
                f"Failed to load prompts: {e}. "
                f"LLM requests will use simple user messages without prompts."
            )
            self.prompt_loader = None

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
            # Pass through OpenAI params from payload.metadata or use default
            openai_opts = payload.metadata.get("openai", {}) if hasattr(payload, 'metadata') and payload.metadata else {}
            raw_result = self._invoke_llm(payload, **openai_opts)
            
            # Parse LLM response - handle both string and dict formats
            if isinstance(raw_result, dict) and "raw_response" in raw_result:
                # Parse the raw_response string (JSON from LLM)
                parsed: ParsedLLMResponse = parse_llm_response(raw_result["raw_response"])
                processing_time_ms = raw_result.get("processing_time_ms")
            elif isinstance(raw_result, dict):
                # Try parsing as dict directly
                parsed: ParsedLLMResponse = parse_llm_response(raw_result)
                processing_time_ms = raw_result.get("processing_time_ms")
            else:
                # String response - parse JSON
                parsed: ParsedLLMResponse = parse_llm_response(str(raw_result))
                processing_time_ms = None
            
            logger.info(f"LLM intent result: intent={parsed.intent}, action_code={parsed.action_code}, confidence={parsed.confidence}")
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
                    "processing_time_ms": processing_time_ms or parsed.processing_time_ms,
                    "reasoning": parsed.reasoning,
                    "prompt_version": self.prompt_loader.version if self.prompt_loader else None,
                },
            }
        except Exception as exc:  # pragma: no cover - defensive safeguard
            logger.error(f"LLM call failed: {exc}")
            fallback = build_fallback_response(reason="llm_failure")
            fallback_metadata = fallback.get("metadata", {})
            fallback_metadata.update({"error": str(exc), **metadata})
            fallback["metadata"] = fallback_metadata
            return {"triggered": True, **fallback}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _invoke_llm(self, payload: LLMIntentRequest, **opts) -> Dict[str, Any]:
        """Call the configured LLM client or fall back to simulation."""

        if self.client is None:
            return self._simulate_llm_response(payload)

        request_body = {
            "messages": self.build_messages(payload),
            "temperature": opts.get("temperature", getattr(self.client, "temperature", 0.3)),
            "max_tokens": opts.get("max_tokens", getattr(self.client, "max_tokens", 400)),
        }
        
        # Extract response from OpenAI client (it returns dict with 'response' key)
        result = self.client.complete(request_body, **opts)
        
        # Handle OpenAI client response format
        if "error" in result:
            logger.error(f"OpenAI client error: {result}")
            raise RuntimeError(f"OpenAI API error: {result.get('error', 'Unknown error')}")
        
        # Extract the actual response text/content
        if "response" in result:
            # OpenAI client returns {"response": "...", "latency_ms": ..., "usage": ...}
            return {
                "intent": None,  # Will be parsed
                "intent_category": None,
                "action_code": None,
                "confidence": None,
                "processing_time_ms": result.get("latency_ms"),
                "reasoning": None,
                "raw_response": result["response"],
            }
        else:
            # Fallback: assume result is the response directly
            return {
                "intent": None,
                "intent_category": None,
                "action_code": None,
                "confidence": None,
                "processing_time_ms": None,
                "reasoning": None,
                "raw_response": result if isinstance(result, str) else str(result),
            }

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

    def build_messages(self, payload: LLMIntentRequest) -> List[Dict[str, str]]:
        """
        Build message array for OpenAI ChatCompletion API.
        
        Uses system prompt and few-shot examples if available, otherwise
        falls back to simple user message.
        
        Args:
            payload: LLM intent request payload
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        if self.prompt_loader is not None:
            try:
                # Production mode: use system prompt + few-shot examples
                messages = self.prompt_loader.build_messages(payload.user_input)
                logger.debug(
                    f"Built messages with system prompt and {len(self.prompt_loader.few_shot_examples)} "
                    f"few-shot examples (version: {self.prompt_loader.version})"
                )
                return messages
            except (PromptLoadError, Exception) as e:
                logger.warning(
                    f"Failed to use prompts, falling back to simple message: {e}"
                )
                # Fallback to simple message if prompt loading fails
                return [
                    {"role": "user", "content": payload.user_input}
                ]
        else:
            # Fallback mode: simple user message only
            logger.debug("Using simple user message (prompts not available)")
            return [
                {"role": "user", "content": payload.user_input}
            ]

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
