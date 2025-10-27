"""
Decision Engine
This file contains the main logic for the intent classification.
"""
from typing import List, Dict, Any

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
            return {
                "status": "CONFIDENT_KEYWORD",
                "intent": keyword_results[0]
            }

        # If rule not met, perform embedding search
        embedding_results = self.embedding_matcher.search(query)

        # Blend scores
        blended_results = self._blend_results(keyword_results, embedding_results)

        if not blended_results:
             print(f"⚠ No match found for query: '{query}'")
             return {
                "status": "NO_MATCH",
                "results": []
            }

        # Evaluate final confidence
        is_confident, reason = confidence_threshold.is_confident(blended_results)

        if is_confident:
            print(f"✅ Blended result is confident. Reason: {reason}")
            return {
                "status": reason,
                "intent": blended_results[0]
            }
        else:
            print(f"⚠ Blended result is NOT confident. Reason: {reason}")
            return {
                "status": reason,
                "results": blended_results
            }

    def _blend_results(self, kw_results: List, emb_results: List) -> List[Dict]:
        """
        Implements weighted scoring to combine results from both methods.
        """
        combined = {}
        
        # Helper to add results
        def add_result(result, score_type, weight):
            intent_id = result.get('id')
            if not intent_id:
                return
            
            score = result.get('score', 0) * weight
            if intent_id not in combined:
                combined[intent_id] = {'kw_score': 0, 'emb_score': 0, 'details': {}}
            
            combined[intent_id][score_type] = score
            combined[intent_id]['details'] = result 

        for res in kw_results:
            add_result(res, 'kw_score', self.kw_weight)
            
        for res in emb_results:
            add_result(res, 'emb_score', self.emb_weight)

        # Calculate final weighted score
        final_results = []
        for intent_id, data in combined.items():
            final_score = round(data['kw_score'] + data['emb_score'], 4)
            if final_score > 0:
                final_obj = data['details'].copy()
                final_obj['id'] = intent_id
                final_obj['intent'] = intent_id
                final_obj['score'] = final_score
                final_obj['blend_scores'] = {'kw': data['kw_score'], 'emb': data['emb_score']}
                final_results.append(final_obj)
        
        # Sort by new blended score
        final_results.sort(key=lambda x: x['score'], reverse=True)
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