# app/ai/intent_classification/hybrid_classifier.py

from .keyword_matcher import KeywordMatcher
from .embedding_matcher import EmbeddingMatcher
from .config import (
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

    Decision Flow:
    1.  The classifier first attempts to find a high-confidence match using the KeywordMatcher.
    2.  If the keyword match returns a result with a confidence score greater than
        the KEYWORD_PRIORITY_THRESHOLD, that result is returned immediately, and the
        embedding-based matching is skipped. This prioritizes explicit keyword matches.
    3.  If the keyword match score is below the threshold or returns no result, the
        classifier proceeds to get results from the EmbeddingMatcher as well.
    4.  If results are available from both methods, their scores are combined using
        a weighted average (defined by KEYWORD_WEIGHT and EMBEDDING_WEIGHT).
    5.  The intent with the highest combined score is then selected as the final result.
    6.  If one method fails to return a result, the result from the other is used.
    7.  If neither method can determine an intent, a fallback response is returned.
    """

    def __init__(self):
        """Initializes the hybrid classifier with its constituent matchers."""
        self.keyword_matcher = KeywordMatcher()
        self.embedding_matcher = EmbeddingMatcher()
        logging.info("HybridClassifier initialized.")

    def classify(self, query: str) -> dict:
        """
        Classifies the user's query to determine the intent.

        Args:
            query (str): The user input text.

        Returns:
            dict: A dictionary containing the determined 'intent' and 'confidence_score',
                  or a fallback intent if classification is unsuccessful.
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
        Handles both matching and conflicting intent results.

        Args:
            keyword_result (dict): The result from the keyword matcher.
            embedding_result (dict): The result from the embedding matcher.

        Returns:
            dict: The final intent and its combined confidence score.
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

# Example of a corresponding configuration file
# You would create a new file named `config.py` inside the `intent_classification` directory.
#
# # app/ai/intent_classification/config.py
#
# # --- Hybrid Classifier Configuration ---
#
# # Priority Rule: If a keyword match confidence is above this value,
# # we will skip the embedding match entirely.
# KEYWORD_PRIORITY_THRESHOLD = 0.90
#
# # Weighted Scoring: Used when both keyword and embedding methods return results
# # below the priority threshold. These weights determine the final blended score.
# # They do not need to sum to 1.
# KEYWORD_WEIGHT = 1.2
# EMBEDDING_WEIGHT = 1.0