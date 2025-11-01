"""
Decision Engine
This file contains the main logic for the intent classification.
Now integrated with config manager for dynamic configuration and A/B testing.
"""
import os
from typing import List, Dict, Any

# --- CONFIG MANAGER INTEGRATION ---
# Import config manager for dynamic configuration
from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT, switch_variant
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS  # Fallback config
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification.hybrid_classifier import HybridClassifier
from app.ai.intent_classification import confidence_threshold
# Optional LLM fallback
try:
    from app.ai.llm_intent.request_handler import RequestHandler as _LLMHandler
    from app.ai.llm_intent.openai_client import OpenAIClient as _OpenAIClient
    from app.schemas.llm_intent import LLMIntentRequest as _LLMReq
except Exception:
    _LLMHandler = None  # type: ignore
    _OpenAIClient = None  # type: ignore
    _LLMReq = None  # type: ignore
# --- END CONFIG MANAGER INTEGRATION ---

class DecisionEngine:
    """
    Orchestrates the hybrid search process.
    Now supports dynamic configuration via config manager.
    """
    def __init__(self):
        """
        Initializes the Decision Engine and its constituent matchers.
        Now uses config manager for dynamic configuration.
        """
        print("Initializing DecisionEngine...")
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

    def search(self, query: str) -> Dict[str, Any]:
        """
        Executes the full hybrid search flow and evaluates confidence.
        Now respects config manager settings for A/B testing.
        """
        # Reload config in case it changed (for hot-reload)
        self._load_config_from_manager()
        
        keyword_results = []
        embedding_results = []
        
        # Use keyword matching if enabled
        if self.use_keywords:
            keyword_results = self.keyword_matcher.search(query)
            
            # Apply the priority rule (if keywords enabled)
            if keyword_results and keyword_results[0]['score'] >= getattr(self, 'priority_threshold', PRIORITY_THRESHOLD):
                print(f"✅ Priority rule triggered. Returning high-confidence keyword match: {keyword_results[0]['id']}")
                return {
                    "status": "CONFIDENT_KEYWORD",
                    "intent": keyword_results[0],
                    "config_variant": ACTIVE_VARIANT
                }
        
        # Use embedding matching if enabled
        if self.use_embedding:
            if self.embedding_matcher is None:
                self.embedding_matcher = EmbeddingMatcher()
            embedding_results = self.embedding_matcher.search(query)
        
        # Blend results if both methods are enabled
        if self.use_keywords and self.use_embedding:
            blended_results = self.hybrid_classifier.blend(keyword_results, embedding_results)
        elif self.use_keywords and keyword_results:
            blended_results = keyword_results
        elif self.use_embedding and embedding_results:
            blended_results = embedding_results
        else:
            blended_results = []

        if not blended_results:
            # Enhanced fallback: try with lower thresholds
            print(f"⚠ No match found for query: '{query}', trying fallback...")
            
            # Fallback 1: Lower embedding threshold
            if embedding_results:
                embedding_results_lower = [r for r in embedding_results if r['score'] >= 0.3]
                if embedding_results_lower:
                    print(f"✅ Fallback found embedding match with lower threshold")
                    return {
                        "status": "FALLBACK_EMBEDDING",
                        "intent": embedding_results_lower[0],
                        "config_variant": ACTIVE_VARIANT
                    }
            
            # Fallback 2: Lower keyword threshold
            if keyword_results:
                keyword_results_lower = [r for r in keyword_results if r['score'] >= 0.3]
                if keyword_results_lower:
                    print(f"✅ Fallback found keyword match with lower threshold")
                    return {
                        "status": "FALLBACK_KEYWORD",
                        "intent": keyword_results_lower[0],
                        "config_variant": ACTIVE_VARIANT
                    }
            
            # Fallback 3: Generic search intent
            print(f"⚠ No specific match found, returning generic search intent")
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

        # Evaluate final confidence
        is_confident, reason = confidence_threshold.is_confident(blended_results)

        if is_confident:
            print(f"✅ Blended result is confident. Reason: {reason}")
            return {
                "status": reason,
                "intent": blended_results[0],
                "config_variant": ACTIVE_VARIANT
            }
        else:
            # Deterministic selection on low-confidence: pick top blended action
            print(f"⚠ Blended result is NOT confident. Reason: {reason}")
            
            # Try queue-based async processing for ambiguous queries (CNS-21)
            # Enabled by default for main endpoint
            # To disable queue: set ENABLE_LLM_QUEUE=false in environment
            enable_queue = os.getenv("ENABLE_LLM_QUEUE", "true").lower() == "true"
            
            if enable_queue:
                try:
                    from app.queue.integration import send_to_llm_queue
                    from app.ai.intent_classification.ambiguity_resolver import detect_intent
                    
                    # Check if this is an ambiguous/unclear query
                    ambiguity_result = detect_intent(query)
                    
                    if ambiguity_result.get("action") in ["AMBIGUOUS", "UNCLEAR"]:
                        # Send to queue for async LLM processing
                        message_id = send_to_llm_queue(
                            query=query,
                            ambiguity_result=ambiguity_result,
                            user_id="anonymous",  # TODO: Get from request context
                            is_premium=False  # TODO: Get from user profile
                        )
                        
                        if message_id:
                            print(f"✅ Sent ambiguous query to queue: {message_id}")
                            # Return a pending status indicating async processing
                            return {
                                "status": "QUEUED_FOR_LLM",
                                "intent": {
                                    "id": "PROCESSING",
                                    "intent": "PROCESSING",
                                    "score": 0.0,
                                    "source": "queue",
                                    "message_id": message_id
                                },
                                "message": "Query sent to LLM queue for processing",
                                "config_variant": ACTIVE_VARIANT
                            }
                except ImportError:
                    # Queue integration not available, continue with sync LLM fallback
                    pass
                except Exception as e:
                    print(f"⚠️ Queue integration error: {e}. Falling back to sync processing.")
            
            # Attempt LLM fallback if available (synchronous)
            if _LLMHandler and _LLMReq and _OpenAIClient:
                try:
                    # Initialize OpenAI client and pass to RequestHandler
                    import os
                    api_key = os.getenv("OPENAI_API_KEY")
                    if not api_key:
                        print("⚠️ OPENAI_API_KEY not set, skipping LLM fallback")
                    else:
                        llm_client = _OpenAIClient()
                        handler = _LLMHandler(client=llm_client)
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
                except Exception as e:
                    print(f"⚠️ LLM fallback error: {e}")
                    import traceback
                    traceback.print_exc()
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



# Global instance for the main API
_decision_engine = None

def get_intent_classification(query: str) -> Dict[str, Any]:
    """
    Main function for intent classification.
    Creates a DecisionEngine instance if needed and processes the query.
    """
    global _decision_engine
    
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    
    return _decision_engine.search(query)