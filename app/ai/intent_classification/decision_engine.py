"""
Decision Engine
This file contains the main logic for the intent classification.
Now integrated with config manager for dynamic configuration and A/B testing.
"""
from typing import List, Dict, Any, Tuple
import logging
import traceback

<<<<<<< HEAD
# --- THIS IS THE FIX (keep 'app.' imports) ---
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS
=======
# --- CONFIG MANAGER INTEGRATION ---
# Import config manager for dynamic configuration
from app.core.config_manager import CONFIG_CACHE, ACTIVE_VARIANT, switch_variant
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS  # Fallback config
>>>>>>> 8ce8b01ca5e8a785c81715269b054287f0d23d52
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification import confidence_threshold
# --- END CONFIG MANAGER INTEGRATION ---

# Minimal logger (so prints are captured in logs)
logger = logging.getLogger("decision_engine")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


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
        logger.info("Initializing DecisionEngine...")
        # Instantiate matchers (assumed to be lightweight)
        self.keyword_matcher = KeywordMatcher()
        self.embedding_matcher = EmbeddingMatcher()
        
<<<<<<< HEAD
        # Load settings from the config file
        self.priority_threshold = PRIORITY_THRESHOLD
        self.kw_weight = WEIGHTS.get("keyword", 0.5)
        self.emb_weight = WEIGHTS.get("embedding", 0.5)
        logger.info("✅ DecisionEngine Initialized: Settings loaded from config.")
=======
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
                # Fallback to static config
                self.use_embedding = True
                self.use_keywords = True
                self.priority_threshold = PRIORITY_THRESHOLD
                self.kw_weight = WEIGHTS["keyword"]
                self.emb_weight = WEIGHTS["embedding"]
                print("📋 Using fallback static config")
                
        except Exception as e:
            # Fallback to static config on any error
            print(f"⚠️ Config manager error, using fallback: {e}")
            self.use_embedding = True
            self.use_keywords = True
            self.priority_threshold = PRIORITY_THRESHOLD
            self.kw_weight = WEIGHTS["keyword"]
            self.emb_weight = WEIGHTS["embedding"]
>>>>>>> 8ce8b01ca5e8a785c81715269b054287f0d23d52

    def search(self, query: str) -> Dict[str, Any]:
        """
        Executes the full hybrid search flow and evaluates confidence.
        Now respects config manager settings for A/B testing.
        """
<<<<<<< HEAD
        try:
            keyword_results: List[Dict[str, Any]] = self.keyword_matcher.search(query) or []
            # Apply the priority rule
            if keyword_results and keyword_results[0].get('score', 0) >= self.priority_threshold:
                logger.info(
                    "✅ Priority rule triggered. Returning high-confidence keyword match: %s", 
                    keyword_results[0].get('id')
                )
                return {"status": "CONFIDENT_KEYWORD", "intent": keyword_results[0]}

            # If rule not met, perform embedding search
            embedding_results: List[Dict[str, Any]] = self.embedding_matcher.search(query) or []

            # Blend scores
            blended_results = self._blend_results(keyword_results, embedding_results)

            if not blended_results:
                # Enhanced fallback: try with lower thresholds
                logger.warning("⚠ No match found for query: '%s', trying fallback...", query)
                
                # Fallback 1: Lower embedding threshold
                if embedding_results:
                    embedding_results_lower = [r for r in embedding_results if r.get('score', 0) >= 0.3]
                    if embedding_results_lower:
                        logger.info("✅ Fallback found embedding match with lower threshold")
                        return {"status": "FALLBACK_EMBEDDING", "intent": embedding_results_lower[0]}
                
                # Fallback 2: Lower keyword threshold
                if keyword_results:
                    keyword_results_lower = [r for r in keyword_results if r.get('score', 0) >= 0.3]
                    if keyword_results_lower:
                        logger.info("✅ Fallback found keyword match with lower threshold")
                        return {"status": "FALLBACK_KEYWORD", "intent": keyword_results_lower[0]}
                
                # Fallback 3: Generic search intent
                logger.warning("⚠ No specific match found, returning generic search intent")
                return {
                    "status": "FALLBACK_GENERIC",
                    "intent": {
                        "id": "SEARCH_PRODUCT",
                        "intent": "SEARCH_PRODUCT", 
                        "score": 0.1,
                        "source": "fallback",
                        "reason": "generic_search_fallback"
                    }
=======
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
            # Enhanced fallback for low confidence results
            print(f"⚠ Blended result is NOT confident. Reason: {reason}")
            
            # If we have any results, return the best one with fallback status
            if blended_results and blended_results[0]['score'] >= 0.1:
                print(f"✅ Returning best available result as fallback")
                return {
                    "status": f"FALLBACK_{reason}",
                    "intent": blended_results[0],
                    "config_variant": ACTIVE_VARIANT
>>>>>>> 8ce8b01ca5e8a785c81715269b054287f0d23d52
                }

            # Evaluate final confidence
            try:
                # support functions that return (bool, reason) or just bool
                is_confident, reason = confidence_threshold.is_confident(blended_results)
            except Exception:
                # If contract differs, try single-bool return
                try:
                    maybe_bool = confidence_threshold.is_confident(blended_results)
                    if isinstance(maybe_bool, bool):
                        is_confident, reason = maybe_bool, "CONFIDENT_BY_THRESHOLD"
                    else:
                        # fallback conservative behavior
                        is_confident, reason = False, "UNKNOWN_CONFIDENCE_FUNCTION"
                except Exception:
                    is_confident, reason = False, "CONFIDENCE_EVAL_ERROR"
                    logger.error("Error calling confidence_threshold: %s", traceback.format_exc())

            if is_confident:
                logger.info("✅ Blended result is confident. Reason: %s", reason)
                return {"status": reason, "intent": blended_results[0]}
            else:
                # Enhanced fallback for low confidence results
                logger.warning("⚠ Blended result is NOT confident. Reason: %s", reason)
                # If we have any results, return the best one with fallback status
                if blended_results and blended_results[0].get('score', 0) >= 0.1:
                    logger.info("✅ Returning best available result as fallback")
                    return {"status": f"FALLBACK_{reason}", "intent": blended_results[0]}

                # Final fallback to generic search
                logger.warning("⚠ No suitable results, returning generic search")
                return {
                    "status": "FALLBACK_GENERIC",
                    "intent": {
                        "id": "SEARCH_PRODUCT",
                        "intent": "SEARCH_PRODUCT", 
                        "score": 0.1,
                        "source": "fallback",
                        "reason": "generic_search_fallback"
                    }
                }
        except Exception as exc:
            logger.exception("Unhandled exception in DecisionEngine.search(): %s", exc)
            # Safe generic fallback on unexpected error
            return {
                "status": "ERROR_FALLBACK",
                "intent": {
                    "id": "SEARCH_PRODUCT",
<<<<<<< HEAD
                    "intent": "SEARCH_PRODUCT",
                    "score": 0.05,
                    "source": "error_fallback",
                    "reason": "internal_error"
                }
=======
                    "intent": "SEARCH_PRODUCT", 
                    "score": 0.1,
                    "source": "fallback",
                    "reason": "generic_search_fallback"
                },
                "config_variant": ACTIVE_VARIANT
>>>>>>> 8ce8b01ca5e8a785c81715269b054287f0d23d52
            }

    def _blend_results(self, kw_results: List[Dict[str, Any]], emb_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Implements sophisticated weighted scoring to combine results from both methods.
        """
<<<<<<< HEAD
        combined: Dict[str, Dict[str, Any]] = {}
        
        # Helper to add results with enhanced conflict resolution
        def add_result(result: Dict[str, Any], score_type: str, weight: float):
            intent_id = result.get('id')
            if not intent_id:
                return
            
            raw_score = float(result.get('score', 0.0) or 0.0)
            weighted_score = raw_score * weight
            if intent_id not in combined:
                combined[intent_id] = {
                    'kw_score': 0.0, 
                    'emb_score': 0.0, 
                    'details': {},
                    'match_count': 0,
                    'max_individual_score': 0.0
                }
            
            combined[intent_id][score_type] = combined[intent_id].get(score_type, 0.0) + weighted_score
            combined[intent_id]['details'] = result
            combined[intent_id]['match_count'] = combined[intent_id].get('match_count', 0) + 1
            combined[intent_id]['max_individual_score'] = max(
                combined[intent_id]['max_individual_score'], raw_score
            )

        # Defensive iteration
        for res in (kw_results or []):
            add_result(res, 'kw_score', self.kw_weight)
            
        for res in (emb_results or []):
            add_result(res, 'emb_score', self.emb_weight)

        # Enhanced scoring with conflict resolution
        final_results: List[Dict[str, Any]] = []
        for intent_id, data in combined.items():
            base_score = data.get('kw_score', 0.0) + data.get('emb_score', 0.0)
            consensus_bonus = 0.1 if data.get('match_count', 0) > 1 else 0.0
            confidence_bonus = min(0.2, data.get('max_individual_score', 0.0) * 0.2)
            final_score = round(base_score + consensus_bonus + confidence_bonus, 4)

            if final_score > 0:
                final_obj = data.get('details', {}).copy()
                final_obj['id'] = intent_id
                final_obj['intent'] = intent_id
                final_obj['score'] = final_score
                final_obj['blend_scores'] = {
                    'kw': data.get('kw_score', 0.0),
                    'emb': data.get('emb_score', 0.0),
                    'consensus_bonus': consensus_bonus,
                    'confidence_bonus': confidence_bonus
                }
                final_obj['match_count'] = data.get('match_count', 0)
                final_obj['max_individual_score'] = data.get('max_individual_score', 0.0)
                final_results.append(final_obj)

        # Sort by final score with tie-breaking
        final_results.sort(key=lambda x: (x.get('score', 0.0), x.get('match_count', 0), x.get('max_individual_score', 0.0)), reverse=True)
        return final_results


# -----------------------------------------------------------------
# --- SINGLETON INSTANCE and PUBLIC FUNCTION ---
# -----------------------------------------------------------------
_engine_instance: DecisionEngine = None
try:
    _engine_instance = DecisionEngine()
except Exception as e:
    logger.exception("🛑 CRITICAL: Failed to initialize DecisionEngine singleton: %s", e)
    _engine_instance = None
=======
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
>>>>>>> 8ce8b01ca5e8a785c81715269b054287f0d23d52


def get_intent_classification(query: str) -> Dict[str, Any]:
    """
    Main function for intent classification.
    Creates a DecisionEngine instance if needed and processes the query.
    """
<<<<<<< HEAD
    # Warm-up path is allowed even if engine failed to initialize
    if query == "warm up":
        logger.info("DecisionEngine warmup call received.")
        return {"status": "warmed_up", "classification_status": "warmed_up", "source": "hybrid_decision_engine"}

    if _engine_instance is None:
        # Fail fast with clear message; caller can decide how to handle
        raise RuntimeError("DecisionEngine is not initialized. Check startup logs for errors.")
        
    # Run the search
    result = _engine_instance.search(query)

    # Standardize output (ensure expected keys)
    result['classification_status'] = result.pop('status', 'UNKNOWN')
    result.setdefault('source', 'hybrid_decision_engine')

    return result
=======
    global _decision_engine
    
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    
    return _decision_engine.search(query)
>>>>>>> 8ce8b01ca5e8a785c81715269b054287f0d23d52
