"""
Decision Engine
Core logic for hybrid intent classification combining keyword and embedding matchers.
Fully integrated with Config Manager for live rule switching and A/B testing.
"""

from typing import List, Dict, Any

# --- CONFIG MANAGER INTEGRATION ---
from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS  # Static fallback configuration
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification.hybrid_classifier import HybridClassifier
from app.ai.intent_classification import confidence_threshold
# Optional LLM fallback
try:
    from app.ai.llm_intent.request_handler import RequestHandler as _LLMHandler
    from app.schemas.llm_intent import LLMIntentRequest as _LLMReq
except Exception:
    _LLMHandler = None  # type: ignore
    _LLMReq = None  # type: ignore
# --- END CONFIG MANAGER INTEGRATION ---

class DecisionEngine:
    """
    Orchestrates the hybrid (keyword + embedding) classification process.
    Supports live A/B config variants and weighted blending logic.
    """

    def __init__(self):
        print("⚙️ Initializing DecisionEngine...")
        self.keyword_matcher = KeywordMatcher()
        # Lazy-load embedding matcher to avoid loading model when disabled or in tests
        self.embedding_matcher = None
        # Initialize hybrid classifier (weights will be updated from config)
        self.hybrid_classifier = HybridClassifier()
        
        # Load settings from config manager (with fallback to static config)
        self._load_config_from_manager()
        print(f"✅ DecisionEngine Initialized: Settings loaded from config manager (variant: {ACTIVE_VARIANT})")
    
    def _load_config_from_manager(self):
        """
        Load configuration from config manager with fallback to static config.
        """
        try:
            # Import here to get fresh values
            from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT
            
            # Try to get rules from config manager (supports nested schema: {"rules": {"rule_sets": {...}}})
            rules_root = CONFIG_CACHE.get('rules', {})
            rules = rules_root.get('rules', rules_root)
            rule_sets = rules.get('rule_sets', {})
            current_rules = rule_sets.get(ACTIVE_VARIANT, {})
            
            # Use config manager settings if available
            if current_rules:
                self.use_embedding = current_rules.get('use_embedding', True)
                self.use_keywords = current_rules.get('use_keywords', True)
                # Load dynamic weights/thresholds if present
                self.kw_weight = current_rules.get('kw_weight', WEIGHTS.get('keyword', 0.6))
                self.emb_weight = current_rules.get('emb_weight', WEIGHTS.get('embedding', 0.4))
                self.priority_threshold = current_rules.get('priority_threshold', PRIORITY_THRESHOLD)
                # Update classifier weights
                self.hybrid_classifier.update_weights(self.kw_weight, self.emb_weight)
                print(
                    f"📋 Using config manager rules for variant {ACTIVE_VARIANT}: "
                    f"embedding={self.use_embedding}, keywords={self.use_keywords}, "
                    f"kw_weight={self.kw_weight}, emb_weight={self.emb_weight}, "
                    f"threshold={self.priority_threshold}"
                )
            else:
                # Fallback to static config (Variant A defaults)
                self.use_embedding = True
                self.use_keywords = True
                self.priority_threshold = 0.85
                self.kw_weight = 0.6
                self.emb_weight = 0.4
                # Update classifier weights
                self.hybrid_classifier.update_weights(self.kw_weight, self.emb_weight)
                print("📋 Using fallback static config (Variant A: kw=0.6, emb=0.4, threshold=0.85)")
                
        except Exception as e:
            # Fallback to static config on any error (Variant A)
            print(f"⚠️ Config manager error, using fallback: {e}")
            self.use_embedding = True
            self.use_keywords = True
            self.priority_threshold = 0.85
            self.kw_weight = 0.6
            self.emb_weight = 0.4
            # Update classifier weights
            self.hybrid_classifier.update_weights(self.kw_weight, self.emb_weight)

    # -------------------------------------------------------------------------
    # MAIN SEARCH LOGIC
    # -------------------------------------------------------------------------
    def search(self, query: str) -> Dict[str, Any]:
        """Main entry point — performs hybrid classification search."""
        self._load_config()  # Hot reload current variant config

        keyword_results, embedding_results = [], []

        # --- Keyword Matcher ---
        if self.use_keywords:
            keyword_results = self.keyword_matcher.search(query)
            if keyword_results and keyword_results[0]["score"] >= self.priority_threshold:
                print(f"✅ Priority Keyword Match: {keyword_results[0]['id']}")
                return self._build_response("CONFIDENT_KEYWORD", keyword_results[0])

        # --- Embedding Matcher ---
        if self.use_embedding:
            if self.embedding_matcher is None:
                self.embedding_matcher = EmbeddingMatcher()
            embedding_results = self.embedding_matcher.search(query)

        # --- Blending Results ---
        if self.use_keywords and self.use_embedding:
            blended_results = self.hybrid_classifier.blend(keyword_results, embedding_results)
        elif self.use_keywords and keyword_results:
            blended_results = keyword_results
        elif self.use_embedding and embedding_results:
            blended_results = embedding_results
        else:
            blended_results = keyword_results or embedding_results

        if not blended_results:
            return self._fallback_no_match(query, keyword_results, embedding_results)

        # --- Confidence Evaluation ---
        is_confident, reason = confidence_threshold.is_confident(blended_results)
        top_result = blended_results[0]

        if is_confident:
            print(f"✅ Confident result → {top_result['intent']} | Reason: {reason}")
            return self._build_response(reason, top_result)
        else:
            # Deterministic selection on low-confidence: pick top blended action
            print(f"⚠ Blended result is NOT confident. Reason: {reason}")
            # Attempt LLM fallback if available
            if _LLMHandler and _LLMReq:
                try:
                    handler = _LLMHandler()
                    # Build minimal LLM request using top keyword/embedding confidences if present
                    top_kw = keyword_results[0]['score'] if keyword_results else 0.0
                    next_kw = keyword_results[1]['score'] if len(keyword_results) > 1 else 0.0
                    llm_req = _LLMReq(
                        user_input=query,
                        rule_intent=blended_results[0]['id'] if blended_results else None,
                        action_code=blended_results[0]['id'] if blended_results else None,
                        top_confidence=float(top_kw),
                        next_best_confidence=float(next_kw),
                        is_fallback=True,
                    )
                    llm_out = handler.handle(llm_req)
                    if llm_out and isinstance(llm_out, dict):
                        # Return LLM-resolved action_code as final
                        resolved = {
                            "id": llm_out.get("action_code"),
                            "intent": llm_out.get("action_code"),
                            "score": llm_out.get("confidence", 0.0),
                            "source": "llm",
                            "reason": "llm_fallback"
                        }
                        return {
                            "status": "LLM_FALLBACK",
                            "intent": resolved,
                            "config_variant": ACTIVE_VARIANT
                        }
                except Exception as _:
                    pass
            if blended_results:
                # If multiple with close scores, prefer one with higher embedding_score
                blended_results.sort(key=lambda x: (x.get('score', 0.0), x.get('embedding_score', 0.0)), reverse=True)
                top = blended_results[0]
                print("✅ Selecting top blended action deterministically")
                return {
                    "status": f"BLENDED_TOP_{reason}",
                    "intent": top,
                    "config_variant": ACTIVE_VARIANT
                }
            # Final fallback to generic search
            print(f"⚠ No suitable results, returning generic search")
            return {
                "status": "FALLBACK_GENERIC",
                "intent": {
                    "id": "SEARCH_PRODUCT",
                    "intent": "SEARCH_PRODUCT",
                    "score": 0.1,
                    "source": "fallback",
                    "reason": "generic_search_fallback"
                },
                "config_variant": ACTIVE_VARIANT
            }


    # -------------------------------------------------------------------------
    # FALLBACK LOGIC
    # -------------------------------------------------------------------------
    def _fallback_no_match(self, query, kw, emb):
        """Handle completely unmatched queries."""
        print(f"⚠️ No confident match found for query → '{query}'")

        if emb:
            emb_fallback = [r for r in emb if r["score"] >= 0.3]
            if emb_fallback:
                print("✅ Fallback embedding match selected.")
                return self._build_response("FALLBACK_EMBEDDING", emb_fallback[0])

        if kw:
            kw_fallback = [r for r in kw if r["score"] >= 0.3]
            if kw_fallback:
                print("✅ Fallback keyword match selected.")
                return self._build_response("FALLBACK_KEYWORD", kw_fallback[0])

        print("⚠️ Defaulting to generic search intent.")
        return self._build_response("FALLBACK_GENERIC", {
            "id": "SEARCH_PRODUCT",
            "intent": "SEARCH_PRODUCT",
            "score": 0.1,
            "source": "fallback",
            "reason": "generic_search_fallback",
        })

    def _fallback_low_confidence(self, results, reason):
        """Fallback handler for low-confidence results."""
        if results and results[0]["score"] >= 0.1:
            print("✅ Using top result as fallback.")
            return self._build_response(f"FALLBACK_{reason}", results[0])

        print("⚠️ No suitable fallback, returning generic search intent.")
        return self._build_response("FALLBACK_GENERIC", {
            "id": "SEARCH_PRODUCT",
            "intent": "SEARCH_PRODUCT",
            "score": 0.1,
            "source": "fallback",
            "reason": "generic_search_fallback",
        })

    # -------------------------------------------------------------------------
    # RESPONSE WRAPPER
    # -------------------------------------------------------------------------
    def _build_response(self, status: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Create a consistent API response format."""
        return {
            "status": status,
            "intent": intent,
            "config_variant": ACTIVE_VARIANT,
        }


# -------------------------------------------------------------------------
# GLOBAL ENTRYPOINT
# -------------------------------------------------------------------------
_decision_engine = None


def get_intent_classification(query: str) -> Dict[str, Any]:
    """Global interface for intent classification API."""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine.search(query)
