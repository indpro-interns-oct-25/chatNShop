"""
Decision Engine
Handles hybrid rule-based + embedding + LLM fallback intent classification.
Now includes resilience, caching, structured logging, and queue-based escalation.
"""
import os
from typing import Dict, Any
import uuid
import traceback
import logging

# --- CONFIG MANAGER INTEGRATION ---
from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT, switch_variant
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification.hybrid_classifier import HybridClassifier
from app.ai.intent_classification import confidence_threshold

# --- QDRANT INTEGRATION ---
try:
    from app.ai.llm_intent.qdrant_cache import store_vector
except Exception:
    store_vector = None

# --- LLM HANDLER / FALLBACK INTEGRATION ---
try:
    from app.ai.llm_intent.request_handler import RequestHandler as _LLMHandler
    from app.ai.llm_intent.openai_client import OpenAIClient as _OpenAIClient
    from app.schemas.llm_intent import LLMIntentRequest as _LLMReq
except Exception:
    _LLMHandler = None
    _OpenAIClient = None
    _LLMReq = None

# --- RESILIENT CLIENT (NEW) ---
try:
    from app.core.resilient_openai_client import resilient_client
except Exception:
    resilient_client = None

# --- ALERT NOTIFIER (NEW ADDITION) ---
try:
    from app.core.alert_notifier import send_alert
except Exception:
    send_alert = None

# --- LOGGER ---
logger = logging.getLogger("decision_engine")
logger.setLevel(logging.INFO)


class DecisionEngine:
    """Orchestrates hybrid search with resilience, caching, and escalation."""

    def __init__(self):
        print("Initializing DecisionEngine...")
        self.keyword_matcher = KeywordMatcher()
        self.embedding_matcher = None
        self.hybrid_classifier = HybridClassifier()
        self._cache: Dict[str, Dict[str, Any]] = {}  # ✅ Local read-through cache
        self._load_config_from_manager()
        print(f"✅ DecisionEngine Initialized: variant={ACTIVE_VARIANT}")

    # ------------------------------------------------------------------
    def _load_config_from_manager(self):
        """Loads config dynamically or uses fallback."""
        try:
            rules_root = CONFIG_CACHE.get("rules", {})
            rules = rules_root.get("rules", rules_root)
            rule_sets = rules.get("rule_sets", {})
            current_rules = rule_sets.get(ACTIVE_VARIANT, {})

            if current_rules:
                self.use_embedding = current_rules.get("use_embedding", True)
                self.use_keywords = current_rules.get("use_keywords", True)
                self.kw_weight = current_rules.get("kw_weight", WEIGHTS.get("keyword", 0.6))
                self.emb_weight = current_rules.get("emb_weight", WEIGHTS.get("embedding", 0.4))
                self.priority_threshold = current_rules.get("priority_threshold", PRIORITY_THRESHOLD)
                self.hybrid_classifier.update_weights(self.kw_weight, self.emb_weight)
                print(f"📋 Using dynamic rules for {ACTIVE_VARIANT}")
            else:
                raise KeyError("Missing dynamic config")

        except Exception as e:
            print(f"⚠️ Config manager error: {e} — Using fallback defaults.")
            self.use_embedding = True
            self.use_keywords = True
            self.priority_threshold = 0.85
            self.kw_weight = 0.6
            self.emb_weight = 0.4
            self.hybrid_classifier.update_weights(self.kw_weight, self.emb_weight)

    # ------------------------------------------------------------------
    def _send_escalation_alert(self, reason: str, query: str):
        """Concrete escalation path integrated with alert_notifier."""
        alert_id = str(uuid.uuid4())
        logger.warning(f"[ALERT:{alert_id}] Escalation: {reason} | Query='{query}'")
        if send_alert:
            try:
                send_alert(
                    event_type=reason,
                    context={
                        "query": query,
                        "alert_id": alert_id,
                        "source": "DecisionEngine",
                    },
                )
            except Exception as e:
                logger.error(f"Failed to send escalation alert: {e}")

    # ------------------------------------------------------------------
    def search(self, query: str) -> Dict[str, Any]:
        """Executes hybrid search + LLM + cache fallback with resilience."""
        correlation_id = str(uuid.uuid4())
        logger.info(f"[{correlation_id}] 🔍 Starting intent classification for: '{query}'")

        # ✅ Cache read-through fallback
        if query in self._cache:
            logger.info(f"[{correlation_id}] Cache hit for query '{query}'")
            return self._cache[query]

        try:
            # Run hybrid classification
            result = self._run_hybrid_search(query)
            self._cache[query] = result  # Cache successful result
            return result

        except Exception as e:
            logger.error(f"[{correlation_id}] Hybrid classification failed: {e}", exc_info=True)
            traceback.print_exc()

            # 🔄 LLM fallback (resilient)
            if resilient_client:
                try:
                    llm_result = resilient_client.call(query)
                    self._send_escalation_alert("LLM_FALLBACK_TRIGGERED", query)
                    result = {
                        "status": "FALLBACK_LLM",
                        "intent": llm_result,
                        "correlation_id": correlation_id,
                    }
                    self._cache[query] = result
                    return result
                except Exception as llm_e:
                    logger.error(f"[{correlation_id}] LLM fallback failed: {llm_e}", exc_info=True)
                    self._send_escalation_alert("LLM_FALLBACK_FAILURE", query)

            # 🧩 Last-good fallback if LLM unavailable
            fallback = {
                "status": "FALLBACK_LAST_GOOD",
                "intent": {
                    "id": "SEARCH_PRODUCT",
                    "intent": "SEARCH_PRODUCT",
                    "score": 0.3,
                    "source": "cached_default",
                },
                "correlation_id": correlation_id,
            }
            self._send_escalation_alert("CACHE_FALLBACK", query)
            self._cache[query] = fallback
            return fallback

    # ------------------------------------------------------------------
    def _run_hybrid_search(self, query: str) -> Dict[str, Any]:
        """Main hybrid + queue-enhanced logic."""
        self._load_config_from_manager()

        keyword_results = []
        embedding_results = []

        if self.use_keywords:
            keyword_results = self.keyword_matcher.search(query)
            if keyword_results and keyword_results[0]["score"] >= self.priority_threshold:
                logger.info(f"✅ High-confidence keyword match: {keyword_results[0]['id']}")
                return {
                    "status": "CONFIDENT_KEYWORD",
                    "intent": keyword_results[0],
                    "config_variant": ACTIVE_VARIANT,
                }

        if self.use_embedding:
            if not self.embedding_matcher:
                self.embedding_matcher = EmbeddingMatcher()
            embedding_results = self.embedding_matcher.search(query)

        if self.use_keywords and self.use_embedding:
            blended_results = self.hybrid_classifier.blend(keyword_results, embedding_results)
        elif self.use_keywords:
            blended_results = keyword_results
        elif self.use_embedding:
            blended_results = embedding_results
        else:
            blended_results = []

        if not blended_results:
            logger.warning(f"⚠ No match found for query '{query}'. Falling back.")
            return self._fallback_generic(query)

        is_confident, reason = confidence_threshold.is_confident(blended_results)
        if is_confident:
            logger.info(f"✅ Blended result is confident. Reason: {reason}")
            return {
                "status": reason,
                "intent": blended_results[0],
                "config_variant": ACTIVE_VARIANT,
            }

        # 🚀 Queue-based fallback + LLM fallback
        logger.warning(f"⚠ Blended result is NOT confident. Reason: {reason}")

        enable_queue = os.getenv("ENABLE_LLM_QUEUE", "true").lower() == "true"
        if enable_queue:
            try:
                from app.queue.integration import send_to_llm_queue
                from app.ai.intent_classification.ambiguity_resolver import detect_intent

                ambiguity_result = detect_intent(query)
                if ambiguity_result.get("action") in ["AMBIGUOUS", "UNCLEAR"]:
                    message_id = send_to_llm_queue(
                        query=query,
                        ambiguity_result=ambiguity_result,
                        user_id="anonymous",
                        is_premium=False,
                    )
                    if message_id:
                        logger.info(f"✅ Sent ambiguous query to queue: {message_id}")
                        return {
                            "status": "QUEUED_FOR_LLM",
                            "intent": {
                                "id": "PROCESSING",
                                "intent": "PROCESSING",
                                "score": 0.0,
                                "source": "queue",
                                "message_id": message_id,
                            },
                            "message": "Query sent to LLM queue for processing",
                            "config_variant": ACTIVE_VARIANT,
                        }
            except Exception as e:
                logger.warning(f"⚠ Queue integration error: {e}. Falling back to sync LLM processing.")

        # Fallback: Sync LLM call
        if _LLMHandler and _LLMReq and _OpenAIClient:
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("⚠ OPENAI_API_KEY not set, skipping LLM fallback")
                else:
                    llm_client = _OpenAIClient()
                    handler = _LLMHandler(client=llm_client)
                    top_kw = keyword_results[0]["score"] if keyword_results else 0.0
                    next_kw = keyword_results[1]["score"] if len(keyword_results) > 1 else 0.0
                    llm_req = _LLMReq(
                        user_input=query,
                        rule_intent=blended_results[0]["id"] if blended_results else None,
                        action_code=blended_results[0]["id"] if blended_results else None,
                        top_confidence=float(top_kw),
                        next_best_confidence=float(next_kw),
                        is_fallback=True,
                    )
                    llm_out = handler.handle(llm_req)
                    if llm_out and isinstance(llm_out, dict):
                        resolved = {
                            "id": llm_out.get("action_code"),
                            "intent": llm_out.get("action_code"),
                            "score": llm_out.get("confidence", 0.0),
                            "source": "llm",
                            "reason": "llm_fallback",
                        }
                        return {
                            "status": "LLM_FALLBACK",
                            "intent": resolved,
                            "config_variant": ACTIVE_VARIANT,
                        }
            except Exception as e:
                logger.error(f"⚠ LLM fallback error: {e}", exc_info=True)

        # Deterministic fallback
        if blended_results:
            blended_results.sort(key=lambda x: (x.get("score", 0.0), x.get("embedding_score", 0.0)), reverse=True)
            top = blended_results[0]
            logger.info("✅ Selecting top blended action deterministically")
            return {
                "status": f"BLENDED_TOP_{reason}",
                "intent": top,
                "config_variant": ACTIVE_VARIANT,
            }

        logger.warning("⚠ No suitable results, returning generic search")
        return self._fallback_generic(query)

    # ------------------------------------------------------------------
    def _fallback_generic(self, query: str) -> Dict[str, Any]:
        """Generic search fallback intent."""
        return {
            "status": "FALLBACK_GENERIC",
            "intent": {
                "id": "SEARCH_PRODUCT",
                "intent": "SEARCH_PRODUCT",
                "score": 0.1,
                "source": "fallback",
            },
            "config_variant": ACTIVE_VARIANT,
        }


# ----------------------------------------------------------------------
# Singleton for app.main
# ----------------------------------------------------------------------
_decision_engine = None


def get_intent_classification(query: str) -> Dict[str, Any]:
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine.search(query)
