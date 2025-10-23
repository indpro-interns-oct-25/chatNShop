# This file assumes you have 'config.py' in the same directory (app/ai/)

try:
    from .. import config
except ImportError:
    # Fallback for direct script execution
    import config
    
from .keyword_matcher import KeywordMatcher
from .embedding_matcher import EmbeddingMatcher
from . import confidence_threshold  # Import the new confidence logic
from typing import List, Dict, Any

class DecisionEngine:
    """
    Orchestrates the hybrid search process, combining keyword and embedding
    results and evaluating the final confidence of the outcome.
    """
    def _init_(self):
        self.keyword_matcher = KeywordMatcher()
        self.embedding_matcher = EmbeddingMatcher()
        
        # Load settings from the config file
        self.priority_threshold = config.PRIORITY_THRESHOLD
        self.kw_weight = config.WEIGHTS["keyword"]
        self.emb_weight = config.WEIGHTS["embedding"]
        print("DecisionEngine Initialized: Settings loaded from config.")

    def search(self, query: str) -> Dict[str, Any]:
        """
        Executes the full hybrid search flow and evaluates confidence.

        Returns:
            A dictionary containing the classification status and results.
            - If confident: {"status": "CONFIDENT", "intent": {...}}
            - If not confident: {"status": "AMBIGUOUS" | "BELOW_THRESHOLD", "results": [...]}
        """
        # 1. Perform keyword search first.
        keyword_results = self.keyword_matcher.search(query)

        # 2. Apply the priority rule for a decisive keyword match.
        if keyword_results and keyword_results[0]['score'] >= self.priority_threshold:
            print("✅ Priority rule triggered. Returning high-confidence keyword match.")
            return {
                "status": "CONFIDENT_KEYWORD",
                "intent": keyword_results[0]
            }

        # 3. If the rule isn't met, perform an embedding search.
        embedding_results = self.embedding_matcher.search(query)

        # 4. Blend the scores from both searchers.
        blended_results = self._blend_results(keyword_results, embedding_results)

        # 5. Evaluate the final blended results for confidence.
        is_confident, reason = confidence_threshold.is_confident(blended_results)

        if is_confident:
            print(f"✅ Blended result is confident. Reason: {reason}")
            return {
                "status": reason,  # e.g., "CONFIDENT"
                "intent": blended_results[0]
            }
        else:
            print(f"⚠ Blended result is NOT confident. Reason: {reason}")
            # The calling function can now use this status to trigger other logic
            # like an ambiguity resolver or a fallback LLM.
            return {
                "status": reason,  # e.g., "AMBIGUOUS" or "BELOW_THRESHOLD"
                "results": blended_results
            }

    def _blend_results(self, kw_results: List, emb_results: List) -> List[Dict]:
        """
        Implements weighted scoring to combine results from both methods.
        """
        combined = {}
        
        for res in kw_results:
            combined[res['id']] = {'kw_score': res['score'], 'emb_score': 0}
            
        for res in emb_results:
            if res['id'] in combined:
                combined[res['id']]['emb_score'] = res['score']
            else:
                combined[res['id']] = {'kw_score': 0, 'emb_score': res['score']}

        # Calculate the final weighted score
        final_results = [
            {
                "id": doc_id,
                "score": round((data['kw_score'] * self.kw_weight) + (data['emb_score'] * self.emb_weight), 4)
            }
            for doc_id, data in combined.items()
        ]
        
        # Filter out results with a score of 0
        final_results = [res for res in final_results if res["score"] > 0]

        # Sort by the new blended score
        final_results.sort(key=lambda x: x['score'], reverse=True)
        return final_results
