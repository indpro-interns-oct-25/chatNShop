"""
Decision Engine
This file contains the main logic for the intent classification.
"""
from typing import Any, Dict, List, Optional

# --- THIS IS THE FIX ---
# All imports must start with 'app.'
from app.ai.config import PRIORITY_THRESHOLD, WEIGHTS
from app.ai.intent_classification.keyword_matcher import KeywordMatcher
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification import confidence_threshold
# --- END FIX ---

class DecisionEngine:
    """
    Orchestrates the hybrid search process.
    """
    def __init__(self):

        """
        Initializes the Decision Engine and its constituent matchers.
        """
        print("Initializing DecisionEngine...")
        self.keyword_matcher = KeywordMatcher()
        self.embedding_matcher = EmbeddingMatcher()
        
        # Load settings from the config file
        self.priority_threshold = PRIORITY_THRESHOLD
        self.kw_weight = WEIGHTS["keyword"]
        self.emb_weight = WEIGHTS["embedding"]
        print("✅ DecisionEngine Initialized: Settings loaded from config.")

    def search(self, query: str) -> Dict[str, Any]:

        """
        Executes the full hybrid search flow and evaluates confidence.
        """
        keyword_results = self.keyword_matcher.search(query)

        # Apply the priority rule
        if keyword_results and keyword_results[0]['score'] >= self.priority_threshold:

            print(f"✅ Priority rule triggered. Returning high-confidence keyword match: {keyword_results[0]['id']}")
            return self._finalize_output(
                status="CONFIDENT_KEYWORD",
                intent=keyword_results[0],
                candidates=keyword_results,
            )

        # If rule not met, perform embedding search
        embedding_results = self.embedding_matcher.search(query)

        # Blend scores
        blended_results = self._blend_results(keyword_results, embedding_results)

        if not blended_results:

            # Enhanced fallback: try with lower thresholds
            print(f"⚠ No match found for query: '{query}', trying fallback...")
            
            # Fallback 1: Lower embedding threshold
            if embedding_results:
                embedding_results_lower = [r for r in embedding_results if r['score'] >= 0.3]
                if embedding_results_lower:
                    print(f"✅ Fallback found embedding match with lower threshold")
                    return self._finalize_output(
                        status="FALLBACK_EMBEDDING",
                        intent=embedding_results_lower[0],
                        candidates=embedding_results_lower,
                        trigger_reason="embedding_low_confidence",
                    )
            
            # Fallback 2: Lower keyword threshold
            if keyword_results:
                keyword_results_lower = [r for r in keyword_results if r['score'] >= 0.3]
                if keyword_results_lower:
                    print(f"✅ Fallback found keyword match with lower threshold")
                    return self._finalize_output(
                        status="FALLBACK_KEYWORD",
                        intent=keyword_results_lower[0],
                        candidates=keyword_results_lower,
                        trigger_reason="keyword_low_confidence",
                    )
            
            # Fallback 3: Generic search intent
            print(f"⚠ No specific match found, returning generic search intent")
            return self._finalize_output(
                status="FALLBACK_GENERIC",
                intent={
                    "id": "SEARCH_PRODUCT",
                    "intent": "SEARCH_PRODUCT",
                    "score": 0.1,
                    "source": "fallback",
                    "reason": "generic_search_fallback",
                },
                trigger_reason="no_match_found",
            )

        # Evaluate final confidence
        is_confident, reason = confidence_threshold.is_confident(blended_results)

        if is_confident:

            print(f"✅ Blended result is confident. Reason: {reason}")
            return self._finalize_output(
                status=reason,
                intent=blended_results[0],
                candidates=blended_results,
            )

        else:
            # Enhanced fallback for low confidence results
            print(f"⚠ Blended result is NOT confident. Reason: {reason}")
            
            # If we have any results, return the best one with fallback status
            if blended_results and blended_results[0]['score'] >= 0.1:
                print(f"✅ Returning best available result as fallback")
                return self._finalize_output(
                    status=f"FALLBACK_{reason}",
                    intent=blended_results[0],
                    candidates=blended_results,
                    trigger_reason=reason,
                )
            
            # Final fallback to generic search
            print(f"⚠ No suitable results, returning generic search")
            return self._finalize_output(
                status="FALLBACK_GENERIC",
                intent={
                    "id": "SEARCH_PRODUCT",
                    "intent": "SEARCH_PRODUCT",
                    "score": 0.1,
                    "source": "fallback",
                    "reason": "generic_search_fallback",
                },
                trigger_reason="no_suitable_results",
            )

    def _finalize_output(
        self,
        *,
        status: str,
        intent: Dict[str, Any],
        candidates: Optional[List[Dict[str, Any]]] = None,
        trigger_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalize the decision engine payload for downstream consumers."""

        normalized_candidates: List[Dict[str, Any]] = []
        if candidates:
            # Ensure we don't mutate the caller-provided list.
            normalized_candidates = [dict(candidate) for candidate in candidates]

        if not normalized_candidates and intent:
            normalized_candidates = [dict(intent)]

        # Guarantee the resolved intent is the first candidate.
        if normalized_candidates and normalized_candidates[0].get("id") != intent.get("id"):
            normalized_candidates.insert(0, dict(intent))

        top_score = normalized_candidates[0].get("score", 0.0) if normalized_candidates else intent.get("score", 0.0) or 0.0
        next_score = normalized_candidates[1].get("score", 0.0) if len(normalized_candidates) > 1 else 0.0

        payload = {
            "status": status,
            "intent": intent,
            "candidates": normalized_candidates,
            "top_confidence": round(float(top_score), 4),
            "next_best_confidence": round(float(next_score), 4),
            "confidence_gap": round(float(top_score - next_score), 4),
            "resolved_intent": intent.get("intent") or intent.get("id"),
            "resolved_action_code": intent.get("action") or intent.get("id"),
            "is_fallback": status.startswith("FALLBACK"),
            "needs_llm_review": not status.upper().startswith("CONFIDENT"),
        }

        if trigger_reason:
            payload["trigger_reason"] = trigger_reason

        return payload

    def _blend_results(self, kw_results: List, emb_results: List) -> List[Dict]:
        """
        Implements sophisticated weighted scoring to combine results from both methods.
        Includes conflict resolution and fallback mechanisms.
        """
        combined = {}
        
        # Helper to add results with enhanced conflict resolution
        def add_result(result, score_type, weight):
            intent_id = result.get('id')
            if not intent_id:
                return
            
            score = result.get('score', 0) * weight
            if intent_id not in combined:
                combined[intent_id] = {
                    'kw_score': 0, 
                    'emb_score': 0, 
                    'details': {},
                    'match_count': 0,
                    'max_individual_score': 0
                }
            
            combined[intent_id][score_type] = score
            combined[intent_id]['details'] = result
            combined[intent_id]['match_count'] += 1
            combined[intent_id]['max_individual_score'] = max(
                combined[intent_id]['max_individual_score'], 
                result.get('score', 0)
            )

        # Add keyword results
        for res in kw_results:
            add_result(res, 'kw_score', self.kw_weight)
            
        # Add embedding results
        for res in emb_results:
            add_result(res, 'emb_score', self.emb_weight)

        # Enhanced scoring with conflict resolution
        final_results = []
        for intent_id, data in combined.items():
            # Base weighted score
            base_score = data['kw_score'] + data['emb_score']
            
            # Bonus for multiple matches (consensus)
            consensus_bonus = 0.1 if data['match_count'] > 1 else 0
            
            # Bonus for high individual scores (confidence)
            confidence_bonus = min(0.2, data['max_individual_score'] * 0.2)
            
            # Final score with bonuses
            final_score = round(base_score + consensus_bonus + confidence_bonus, 4)
            
            if final_score > 0:
                final_obj = data['details'].copy()
                final_obj['id'] = intent_id
                final_obj['intent'] = intent_id
                final_obj['score'] = final_score
                final_obj['blend_scores'] = {
                    'kw': data['kw_score'], 
                    'emb': data['emb_score'],
                    'consensus_bonus': consensus_bonus,
                    'confidence_bonus': confidence_bonus
                }
                final_obj['match_count'] = data['match_count']
                final_obj['max_individual_score'] = data['max_individual_score']
                final_results.append(final_obj)
        
        # Sort by final score with tie-breaking
        final_results.sort(key=lambda x: (x['score'], x['match_count'], x['max_individual_score']), reverse=True)
        return final_results


# -----------------------------------------------------------------
# --- SINGLETON INSTANCE and PUBLIC FUNCTION ---
# -----------------------------------------------------------------
try:
    _engine_instance = DecisionEngine()
except Exception as e:
    print(f"🛑 CRITICAL: Failed to initialize DecisionEngine singleton: {e}")
    _engine_instance = None

def get_intent_classification(query: str) -> Dict[str, Any]:
    """
    This is the main function imported by the FastAPI app.
    """
    if _engine_instance is None:
        raise RuntimeError("DecisionEngine is not initialized. Check startup logs for errors.")
        
    if query == "warm up":
        print("DecisionEngine warmup call received.")
        return {"status": "warmed_up"}
        
    # Run the search
    result = _engine_instance.search(query)
    
    # Standardize output
    result['classification_status'] = result.pop('status', 'UNKNOWN')
    result['source'] = 'hybrid_decision_engine'
    
    return result