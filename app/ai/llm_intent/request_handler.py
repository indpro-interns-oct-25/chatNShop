"""Handles LLM-based intent classification with robust fallback, logging, and error handling."""

from __future__ import annotations

import os
import time
import random
import logging
from typing import Dict, Any, List, Optional
from app.schemas.llm_intent import LLMIntentRequest

# ---------------------------------------------------------------------
# External Integrations (from other branch)
# ---------------------------------------------------------------------
from .confidence_calibrator import TriggerContext, should_trigger_llm
from .entity_extractor import INTENT_CATEGORIES
from .fallback_manager import build_fallback_response
from .openai_client import OpenAIClient
from .response_parser import LLMIntentResponse as ParsedLLMResponse, parse_llm_response
from .prompt_loader import PromptLoader, PromptLoadError, get_prompt_loader

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
from .context_collector import get_context_collector
from .context_summarizer import get_context_summarizer
from .response_cache import get_response_cache
import logging
import os

logger = logging.getLogger("request_handler")

# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------
MAX_RETRIES = 3
RETRY_BACKOFF = [1, 2, 4]  # exponential backoff in seconds


class RequestHandler:
    """Manages LLM intent classification with fallback, retry resilience, and prompt-based coordination."""

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
        self.simulate_mode = True  # True = simulation when no API key
        self.client = client or OpenAIClient()
        try:
            self.prompt_loader = prompt_loader or get_prompt_loader()
            logger.info("RequestHandler initialized with prompt loader")
        except PromptLoadError as e:
            logger.warning(
                f"Failed to load prompts: {e}. "
                f"LLM requests will use simple user messages without prompts."
            )
            self.prompt_loader = None
        
        # Initialize context collector and summarizer
        self.context_collector = get_context_collector()
        
        # Get token limit from environment or use default
        context_token_limit = int(os.getenv("CONTEXT_TOKEN_LIMIT", "2000"))
        self.context_summarizer = get_context_summarizer(max_tokens=context_token_limit)
        
        # Initialize response cache
        self.response_cache = get_response_cache()
        
        # Configuration
        self.enable_context = os.getenv("ENABLE_SESSION_CONTEXT", "true").lower() == "true"
        self.context_history_limit = int(os.getenv("CONTEXT_HISTORY_LIMIT", "5"))

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

            # Retry delay
            if attempt < MAX_RETRIES:
                delay = RETRY_BACKOFF[attempt - 1]
                logging.info(f"⏳ Retrying in {delay}s...")
                time.sleep(delay)

        # 3️⃣ All attempts failed — escalate and return fallback
        logging.critical("🚨 All LLM attempts failed. Triggering escalation path.")
        self._escalate_failure(request)
        return self._fallback_unclear_response(request)

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------
    def _query_llm(self, request: LLMIntentRequest) -> Dict[str, Any]:
        """Simulate or query an external LLM service."""
        if self.simulate_mode:
            text = request.user_input.lower()

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

        # Real LLM Invocation (if simulate_mode = False)
        try:
            messages = self.build_messages(request)
            result = self.client.complete(
                {"messages": messages, "temperature": 0.3, "max_tokens": 400}
            )

            if "error" in result:
                raise RuntimeError(f"OpenAI API error: {result['error']}")

            parsed: ParsedLLMResponse = parse_llm_response(result.get("response", ""))
            logger.info(
                f"LLM intent result: intent={parsed.intent}, action_code={parsed.action_code}, confidence={parsed.confidence}"
            )

                # String response - parse JSON
                parsed: ParsedLLMResponse = parse_llm_response(str(raw_result))
                processing_time_ms = None
            
            # Extract and merge entities (LLM + rule-based fallback)
            entities = self._extract_and_merge_entities(payload.user_input, parsed.entities)
            
            logger.info(
                f"LLM intent result: intent={parsed.intent}, action_code={parsed.action_code}, "
                f"confidence={parsed.confidence}, entities={'present' if entities else 'none'}"
            )
            
            return {
                "triggered": True,
                "intent": parsed.intent,
                "intent_category": parsed.intent_category,
                "action_code": parsed.action_code,
                "confidence": parsed.confidence,
                "requires_clarification": False,
                "clarification_message": None,
                "entities": entities,  # NEW: Include entities in response
                "metadata": {
                    "source": "llm",
                    "processing_time_ms": result.get("latency_ms"),
                    "reasoning": parsed.reasoning,
                    "prompt_version": self.prompt_loader.version if self.prompt_loader else None,
                },
                "status": "LLM_RESULT",
                "variant": "A"
            }
        except Exception as exc:
            logger.error(f"LLM call failed: {exc}")
            fallback = build_fallback_response(reason="llm_failure")
            fallback["metadata"].update({"error": str(exc), "source": "llm"})
            return {"triggered": True, **fallback}

    # -----------------------------------------------------------------
    # Supporting methods
    # -----------------------------------------------------------------
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
        # Check cache first if enabled
        if self.response_cache.enabled:
            cached_response = self.response_cache.get(
                query=payload.user_input,
                context=payload.metadata if hasattr(payload, 'metadata') else None
            )
            if cached_response:
                logger.info(f"✅ Using cached LLM response for query: '{payload.user_input[:50]}...'")
                # Add cache indicator to metadata
                if isinstance(cached_response, dict):
                    cached_response = cached_response.copy()
                    cached_response['_from_cache'] = True
                return cached_response

        # Cache miss - call LLM API
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
            llm_response = {
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
            llm_response = {
                "intent": None,
                "intent_category": None,
                "action_code": None,
                "confidence": None,
                "processing_time_ms": None,
                "reasoning": None,
                "raw_response": result if isinstance(result, str) else str(result),
            }
        
        # Cache the response if enabled
        if self.response_cache.enabled:
            self.response_cache.set(
                query=payload.user_input,
                response=llm_response,
                context=payload.metadata if hasattr(payload, 'metadata') else None
            )
        
        return llm_response

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

    def _escalate_failure(self, request: LLMIntentRequest):
        """Escalate after all retries fail."""
        logging.critical(
            f"🚨 ESCALATION_NEEDED: LLM completely failed for input '{request.user_input}' "
            f"(rule_intent={request.rule_intent}, attempts={MAX_RETRIES})"
        )

    # -----------------------------------------------------------------
    # Message Builder (from other branch)
    # -----------------------------------------------------------------
    def build_messages(self, payload: LLMIntentRequest) -> List[Dict[str, str]]:
        """
        Build message array for OpenAI ChatCompletion API.
        
        Uses system prompt and few-shot examples if available, otherwise
        falls back to simple user message.
        Enhances with context if available.
        
        Args:
            payload: LLM intent request payload
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys
        """
        # Collect and enhance context
        context = None
        if self.enable_context:
            try:
                # Extract user_id and session_id from metadata or context_snippets
                user_id = payload.metadata.get("user_id") if payload.metadata else None
                session_id = payload.metadata.get("session_id") if payload.metadata else None
                
                # Collect conversation history from context_snippets or metadata
                conversation_history = []
                if payload.context_snippets:
                    # Convert context_snippets to conversation history format
                    conversation_history = [
                        {"role": "user", "content": snippet} if isinstance(snippet, str)
                        else snippet
                        for snippet in payload.context_snippets
                    ]
                
                # Collect all context
                raw_context = self.context_collector.collect_all_context(
                    conversation_history=conversation_history,
                    user_id=user_id,
                    session_id=session_id,
                    history_limit=self.context_history_limit
                )
                
                # Summarize to fit token limit
                context = self.context_summarizer.truncate_context(raw_context)
                
                logger.debug(f"Enhanced prompt with context: {len(context.get('conversation_history', []))} messages")
            except Exception as e:
                logger.warning(f"⚠️ Failed to collect/enhance context: {e}")
                context = None
        
        if self.prompt_loader is not None:
            try:
                messages = self.prompt_loader.build_messages(payload.user_input)
                logger.debug(
                    f"Built messages with system prompt and few-shot examples "
                    f"(version: {self.prompt_loader.version})"
                )
                return messages
            except (PromptLoadError, Exception) as e:
                logger.warning(f"Failed to use prompts, fallback to simple message: {e}")
                return [{"role": "user", "content": payload.user_input}]
        else:
            return [{"role": "user", "content": payload.user_input}]
                # Production mode: use system prompt + few-shot examples + context
                messages = self.prompt_loader.build_messages(
                    user_query=payload.user_input,
                    context=context
                )
                logger.debug(
                    f"Built messages with system prompt, {len(self.prompt_loader.few_shot_examples)} "
                    f"few-shot examples, and context (version: {self.prompt_loader.version})"
                )
                return messages
            except (PromptLoadError, Exception) as e:
                logger.warning(
                    f"Failed to use prompts, falling back to simple message: {e}"
                )
                # Fallback to simple message with context if available
                if context and self.prompt_loader:
                    formatted_context = self.prompt_loader.format_context(context)
                    if formatted_context:
                        content = f"{formatted_context}\n\n## Current Query:\n{payload.user_input}"
                        return [{"role": "user", "content": content}]
                return [
                    {"role": "user", "content": payload.user_input}
                ]
        else:
            # Fallback mode: simple user message with context if available
            if context and self.prompt_loader:
                formatted_context = self.prompt_loader.format_context(context)
                if formatted_context:
                    content = f"{formatted_context}\n\n## Current Query:\n{payload.user_input}"
                    return [{"role": "user", "content": content}]
            
            logger.debug("Using simple user message (prompts not available)")
            return [
                {"role": "user", "content": payload.user_input}
            ]

    def _extract_and_merge_entities(self, user_query: str, llm_entities: Any) -> Optional[Dict[str, Any]]:
        """
        Extract and merge entities from LLM and rule-based sources.
        
        Strategy:
        1. If LLM entities are complete, use them
        2. Otherwise, extract via rule-based fallback
        3. Merge both sources (LLM takes precedence)
        
        Args:
            user_query: User input query
            llm_entities: Entities extracted by LLM (Entities object or None)
            
        Returns:
            Merged entities dict or None
        """
        try:
            # Import entity extractor
            from app.ai.entity_extraction.extractor import EntityExtractor
            from app.ai.entity_extraction.schema import Entities
            
            # Check if LLM entities are sufficient
            llm_has_entities = False
            if llm_entities and hasattr(llm_entities, 'product_type'):
                # Check if at least one meaningful entity is present
                llm_has_entities = any([
                    llm_entities.product_type,
                    llm_entities.brand,
                    llm_entities.category,
                    llm_entities.color,
                    llm_entities.size,
                    (llm_entities.price_range and (
                        llm_entities.price_range.min or llm_entities.price_range.max
                    ))
                ])
            
            # If LLM has complete entities, use them directly
            if llm_has_entities:
                logger.debug("Using entities from LLM (complete)")
                if hasattr(llm_entities, 'dict'):
                    return llm_entities.dict()
                else:
                    return llm_entities.__dict__ if hasattr(llm_entities, '__dict__') else None
            
            # Otherwise, fall back to rule-based extraction
            logger.debug("Falling back to rule-based entity extraction")
            extractor = EntityExtractor()
            rule_entities = extractor.extract_entities(user_query)
            
            # If no LLM entities, return rule-based directly
            if not llm_entities:
                logger.debug("Using entities from rule-based extraction")
                return rule_entities
            
            # Merge: LLM takes precedence, rule-based fills gaps
            merged = rule_entities.copy() if rule_entities else {}
            
            if hasattr(llm_entities, 'dict'):
                llm_dict = llm_entities.dict()
            elif hasattr(llm_entities, '__dict__'):
                llm_dict = llm_entities.__dict__
            else:
                llm_dict = {}
            
            # Override with LLM values where present
            for key, value in llm_dict.items():
                if value is not None:
                    if key == 'price_range' and hasattr(value, 'dict'):
                        merged[key] = value.dict()
                    elif key == 'price_range' and isinstance(value, dict):
                        merged[key] = value
                    else:
                        merged[key] = value
            
            logger.debug(f"Merged entities: LLM + rule-based")
            return merged if merged else None
            
        except ImportError:
            logger.warning("Entity extraction module not available")
            # Return LLM entities as-is if available
            if llm_entities:
                if hasattr(llm_entities, 'dict'):
                    return llm_entities.dict()
                elif hasattr(llm_entities, '__dict__'):
                    return llm_entities.__dict__
            return None
        except Exception as e:
            logger.error(f"Error extracting/merging entities: {e}", exc_info=True)
            return None
    
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
