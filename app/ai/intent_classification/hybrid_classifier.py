# app/ai/intent_classification/hybrid_classifier.py

from .keyword_matcher import KeywordMatcher
from .embedding_matcher import EmbeddingMatcher
# --- FIX #1: Corrected relative import to go one level up ---
from ..config import (
    KEYWORD_PRIORITY_THRESHOLD,
    KEYWORD_WEIGHT,
    EMBEDDING_WEIGHT
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HybridClassifier:
    """
    Orchestrates intent classification by combining keyword and embedding-based matching.
    ... (rest of docstring) ...
    """

    # --- FIX #2: Corrected typo from _init_ to __init__ ---
    def __init__(self):
        """Initializes the hybrid classifier with its constituent matchers."""
        self.keyword_matcher = KeywordMatcher()
        self.embedding_matcher = EmbeddingMatcher()
        logging.info("HybridClassifier initialized.")

    def classify(self, query: str) -> dict:
        """
        Classifies the user's query to determine the intent.
        ... (rest of function) ...
        """
        keyword_result = self.keyword_matcher.match(query)
        
        # Priority Rule: If keyword match is strong enough, use it exclusively.
        if keyword_result and keyword_result['confidence_score'] > KEYWORD_PRIORITY_THRESHOLD:
            logging.info(f"High-confidence keyword match found. Skipping embedding search. Intent: {keyword_result['intent']}")
            return keyword_result

        # If keyword match is not decisive, get embedding match result.
        embedding_result = self.embedding_matcher.match(query)

        # Handle cases where one or both matchers return no result.
        if not keyword_result and not embedding_result:
            logging.warning(f"No intent found for query: '{query}'")
            return {'intent': 'fallback_unknown', 'confidence_score': 0.0}
        
        if not keyword_result:
            logging.info(f"Only embedding match found. Intent: {embedding_result['intent']}")
            return embedding_result
            
        if not embedding_result:
            logging.info(f"Only keyword match found (below threshold). Intent: {keyword_result['intent']}")
            return keyword_result

        # If both methods return results, combine them with weighted scoring.
        return self._combine_scores(keyword_result, embedding_result)

    def _combine_scores(self, keyword_result: dict, embedding_result: dict) -> dict:
        """
        Combines results from both matchers using weighted scoring.
        ... (rest of function) ...
        """
        logging.info("Combining scores from keyword and embedding matchers.")
        
        combined_scores = {}

        # Add keyword score with its weight
        kw_intent = keyword_result['intent']
        kw_score = keyword_result['confidence_score']
        combined_scores[kw_intent] = combined_scores.get(kw_intent, 0) + (kw_score * KEYWORD_WEIGHT)

        # Add embedding score with its weight
        emb_intent = embedding_result['intent']
        emb_score = embedding_result['confidence_score']
        combined_scores[emb_intent] = combined_scores.get(emb_intent, 0) + (emb_score * EMBEDDING_WEIGHT)
        
        # Determine the best intent from the combined scores
        if not combined_scores:
            return {'intent': 'fallback_error', 'confidence_score': 0.0}

        best_intent = max(combined_scores, key=combined_scores.get)
        final_score = combined_scores[best_intent]

        # Normalize the score to be within a 0-1 range if needed, though not strictly necessary
        # final_score = final_score / (KEYWORD_WEIGHT + EMBEDDING_WEIGHT)

        logging.info(f"Combined scoring result. Best intent: {best_intent} with score: {final_score:.4f}")
        
        return {'intent': best_intent, 'confidence_score': float(f"{final_score:.4f}")}
