<<<<<<< HEAD
"""Handles LLM-based intent classification with robust fallback, logging, and error handling."""
=======
"""Coordinator that applies trigger logic, invokes the LLM, and normalizes output."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b

import os
import time
import random
import logging
from typing import Dict, Any
from app.schemas.llm_intent import LLMIntentRequest

<<<<<<< HEAD
# ---------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "llm_intent.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]  # exponential backoff in seconds
=======
from .confidence_calibrator import TriggerContext, should_trigger_llm
from .entity_extractor import INTENT_CATEGORIES
from .fallback_manager import build_fallback_response
from .openai_client import OpenAIClient
from .response_parser import LLMIntentResponse as ParsedLLMResponse, parse_llm_response
from .prompt_loader import PromptLoader, PromptLoadError, get_prompt_loader
import logging

logger = logging.getLogger("request_handler")
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b


class RequestHandler:
    """Manages LLM intent classification with fallback and retry resilience."""

<<<<<<< HEAD
    def __init__(self):
        self.simulate_mode = True  # True = no API key required, simulate LLM output
=======
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
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b

    # -----------------------------------------------------------------
    # Main entry point
    # -----------------------------------------------------------------
    def handle(self, request: LLMIntentRequest) -> Dict[str, Any]:
        """Handle an intent classification request with retries and fallbacks."""

        logging.info(f"🔍 Received input: '{request.user_input}'")

        # 1️⃣ High-confidence rule-based intent: no LLM required
        if request.top_confidence >= 0.85 and not request.is_fallback:
            logging.info("✅ Rule-based classifier confident, skipping LLM call.")
            return self._retain_rule_result(request)

        # 2️⃣ Otherwise: attempt LLM classification with retries
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logging.info(f"🧠 Attempt {attempt} to query LLM...")
                result = self._query_llm(request)
                if result:
                    logging.info(f"✅ LLM succeeded on attempt {attempt}.")
                    return result
            except TimeoutError:
                logging.warning(f"⚠️ Timeout occurred on attempt {attempt}.")
            except Exception as e:
                logging.error(f"❌ Error on attempt {attempt}: {str(e)}")

<<<<<<< HEAD
            # Retry delay
            if attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF[attempt - 1]
                logging.info(f"⏳ Retrying in {delay}s...")
                time.sleep(delay)
=======
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
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b

        # 3️⃣ All attempts failed — escalate and return fallback
        logging.critical("🚨 All LLM attempts failed. Triggering escalation path.")
        self._escalate_failure(request)
        return self._fallback_unclear_response(request)

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

<<<<<<< HEAD
    def _query_llm(self, request: LLMIntentRequest) -> Dict[str, Any]:
        """Simulate or query an external LLM service."""
        if self.simulate_mode:
            text = request.user_input.lower()
=======
    def _invoke_llm(self, payload: LLMIntentRequest, **opts) -> Dict[str, Any]:
        """Call the configured LLM client or fall back to simulation."""
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b

            # Simulated intent predictions
            if "remove" in text and "cart" in text:
                return self._build_response("REMOVE_FROM_CART", 0.93, request)
            elif "add" in text and "cart" in text:
                return self._build_response("ADD_TO_CART", 0.91, request)
            elif "wishlist" in text or "save for later" in text:
                return self._build_response("ADD_TO_WISHLIST", 0.89, request)
            elif "checkout" in text:
                return self._build_response("VIEW_CART", 0.86, request)
            elif "total" in text or "price" in text:
                return self._build_response("CART_TOTAL", 0.88, request)
            elif "empty" in text and "cart" in text:
                return self._build_response("EMPTY_CART", 0.87, request)
            else:
                return self._fallback_unclear_response(request)

<<<<<<< HEAD
        # Production (real API) — replace with actual API call
        raise TimeoutError("LLM API not available or network issue.")

    def _retain_rule_result(self, request: LLMIntentRequest) -> Dict[str, Any]:
        """Return rule-based classification directly."""
        return {
            "triggered": False,
            "intent": request.rule_intent or "UNKNOWN",
            "intent_category": "rule_based",
            "action_code": request.action_code or "NONE",
            "confidence": request.top_confidence,
            "requires_clarification": False,
            "clarification_message": None,
            "metadata": {
                "source": "rule_pipeline",
                "reason": "high_confidence",
                "fallback": False
            },
            "status": "RULE_CONFIDENT",
            "variant": "A"
        }
=======
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
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b

    def _fallback_unclear_response(self, request: LLMIntentRequest) -> Dict[str, Any]:
        """Return fallback intent when LLM is uncertain or fails."""
        clarification_msg = "I couldn't determine your intent clearly. Could you clarify what you meant?"

        fallback = {
            "triggered": True,
            "intent": "UNCLEAR",
            "intent_category": "uncertain",
            "action_code": "REQUEST_CLARIFICATION",
            "confidence": 0.0,
            "requires_clarification": True,
            "clarification_message": clarification_msg,
            "suggested_questions": [
                "Do you want to remove something from your cart?",
                "Are you trying to add a product?",
                "Would you like to view or clear your cart?",
            ],
            "metadata": {
                "source": "LLM",
                "reason": "fallback_unclear",
                "attempts": MAX_RETRIES,
                "variant": "A",
            },
            "status": "UNCLEAR",
            "variant": "A"
        }

        logging.warning(f"🤔 Fallback triggered for unclear intent: '{request.user_input}'")
        return fallback

    def _build_response(self, intent: str, confidence: float, request: LLMIntentRequest) -> Dict[str, Any]:
        """Helper to construct standardized LLM response structure."""
        logging.info(f"🧩 Intent classified as {intent} (confidence={confidence:.2f})")

        return {
            "triggered": True,
            "intent": intent,
            "intent_category": "llm",
            "action_code": intent,
            "confidence": confidence,
            "requires_clarification": False,
            "clarification_message": None,
            "metadata": {
                "source": "LLM",
                "reason": "model_prediction",
                "input": request.user_input,
                "variant": "A"
            },
            "status": "LLM_RESULT",
            "variant": "A"
        }

<<<<<<< HEAD
    def _escalate_failure(self, request: LLMIntentRequest):
        """Escalate after all retries fail."""
        logging.critical(
            f"🚨 ESCALATION_NEEDED: LLM completely failed for input '{request.user_input}' "
            f"(rule_intent={request.rule_intent}, attempts={MAX_RETRIES})"
        )
=======
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
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b
