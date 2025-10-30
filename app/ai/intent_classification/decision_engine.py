"""
Decision Engine
This file contains the main logic for the intent classification.
Now integrated with config manager for dynamic configuration and A/B testing.
"""
from typing import List, Dict, Any

# --- CONFIG MANAGER INTEGRATION ---
# Import config manager for dynamic configuration
from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT, switch_variant
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS  # Fallback config
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
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
            
            # Try to get rules from config manager
            rules = CONFIG_CACHE.get('rules', {})
            rule_sets = rules.get('rule_sets', {})
            current_rules = rule_sets.get(ACTIVE_VARIANT, {})
            
            # Use config manager settings if available
            if current_rules:
                self.use_embedding = current_rules.get('use_embedding', True)
                self.use_keywords = current_rules.get('use_keywords', True)
                print(f"📋 Using config manager rules for variant {ACTIVE_VARIANT}: embedding={self.use_embedding}, keywords={self.use_keywords}")
            else:
                # Fallback to static config (biased to embeddings for production)
                self.use_embedding = True
                self.use_keywords = True
                self.priority_threshold = 0.90
                self.kw_weight = 0.4
                self.emb_weight = 0.6
                print("📋 Using fallback static config (Variant B: kw=0.4, emb=0.6, threshold=0.90)")
                
        except Exception as e:
            # Fallback to static config on any error (Variant B)
            print(f"⚠️ Config manager error, using fallback: {e}")
            self.use_embedding = True
            self.use_keywords = True
            self.priority_threshold = 0.90
            self.kw_weight = 0.4
            self.emb_weight = 0.6

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
            blended_results = self._blend_results(keyword_results, embedding_results)
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

    def _blend_results(self, kw_results: List, emb_results: List) -> List[Dict]:
        """
        Implements sophisticated weighted scoring to combine results from both methods.
        """
        if not kw_results and not emb_results:
            return []
        
        if not kw_results:
            return emb_results
        
        if not emb_results:
            return kw_results
        
        # Create a mapping of intent IDs to their scores from both methods
        intent_scores = {}
        
        # Process keyword results
        for result in kw_results:
            intent_id = result.get('id', result.get('intent', 'unknown'))
            score = result.get('score', 0.0)
            intent_scores[intent_id] = {
                'keyword_score': score,
                'keyword_result': result,
                'embedding_score': 0.0,
                'embedding_result': None
            }
        
        # Process embedding results
        for result in emb_results:
            intent_id = result.get('id', result.get('intent', 'unknown'))
            score = result.get('score', 0.0)
            
            if intent_id in intent_scores:
                intent_scores[intent_id]['embedding_score'] = score
                intent_scores[intent_id]['embedding_result'] = result
            else:
                intent_scores[intent_id] = {
                    'keyword_score': 0.0,
                    'keyword_result': None,
                    'embedding_score': score,
                    'embedding_result': result
                }
        
        # Calculate blended scores
        blended_results = []
        kw_weight = getattr(self, 'kw_weight', WEIGHTS["keyword"])
        emb_weight = getattr(self, 'emb_weight', WEIGHTS["embedding"])
        
        for intent_id, scores in intent_scores.items():
            # Weighted average of scores
            blended_score = (scores['keyword_score'] * kw_weight + 
                           scores['embedding_score'] * emb_weight)
            
            # Use the result with higher individual score as base
            if scores['keyword_score'] > scores['embedding_score']:
                base_result = scores['keyword_result']
            else:
                base_result = scores['embedding_result']
            
            if base_result:
                blended_result = base_result.copy()
                blended_result['score'] = blended_score
                blended_result['source'] = 'blended'
                blended_result['keyword_score'] = scores['keyword_score']
                blended_result['embedding_score'] = scores['embedding_score']
                blended_results.append(blended_result)
        
        # Sort by blended score
        blended_results.sort(key=lambda x: x['score'], reverse=True)
        return blended_results


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