"""
embedding_matcher.py
Implements pre-trained embedding-based semantic similarity matching for user intents.
"""

import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any

# --- FIXED IMPORTS ---
from app.ai.intent_classification.keyword_matcher import match_keywords
from app.ai.llm_intent.qdrant_cache import store_vector
# --- END FIX ---

class EmbeddingMatcher:
    """
    A class-based wrapper for the functional embedding matcher.
    """

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initializes the matcher, loads the model, and pre-computes embeddings.
        """
        print(f"🔄 Loading model '{model_name}'...")
        start_time = time.time()

        self.model = SentenceTransformer(model_name)
        self.intent_examples = INTENT_EXAMPLES
        self.intent_embeddings = self._precompute_embeddings()

        print(f"✅ EmbeddingMatcher ready. Model loaded in {time.time() - start_time:.2f}s")

    def _precompute_embeddings(self) -> Dict[str, Any]:
        """Pre-computes and caches the embeddings for all example phrases."""
        embeddings = {}
        for intent, phrases in self.intent_examples.items():
            embeddings[intent] = self.model.encode(phrases, convert_to_tensor=True)
        return embeddings

    def search(self, query: str, threshold: float = 0.60) -> List[Dict]:
        """
        Matches user query to the closest intent using embeddings.
        Includes Qdrant storage for analytics and caching.
        """
        try:
            if not query or not query.strip():
                return []

            clean_query = query.strip().lower()
            if len(clean_query) < 2:
                return []

            query_emb = self.model.encode(clean_query, convert_to_tensor=True)
            results = []

            # Compute similarity across intents
            for intent, ref_emb in self.intent_embeddings.items():
                if ref_emb is not None:
                    sim = util.cos_sim(query_emb, ref_emb).max().item()
                    if sim >= 0.1:
                        results.append({
                            "id": intent,
                            "intent": intent,
                            "score": round(sim, 4),
                            "source": "embedding",
                            "query": clean_query
                        })

            results.sort(key=lambda x: x['score'], reverse=True)

            # ✅ Store best match to Qdrant
            if results:
                best = results[0]
                status = "CONFIDENT" if best["score"] >= threshold else "FALLBACK_BELOW_THRESHOLD"
                store_vector(
                    intent=best["intent"],
                    vector=query_emb.tolist(),
                    confidence=best["score"],
                    status=status,
                    variant="A",
                    query=clean_query
                )

            return results

        except Exception as e:
            print(f"❌ Error during embedding matching: {e}")
            return [{
                "id": "SEARCH_PRODUCT",
                "intent": "SEARCH_PRODUCT",
                "score": 0.1,
                "source": "embedding_fallback",
                "error": str(e)
            }]


# --- Intent examples used for embeddings ---
INTENT_EXAMPLES = {
    "SEARCH": [
        "find this item", "show me products", "search for shoes", "look up phone covers",
    ],
    "ADD_TO_CART": [
        "add this to my basket", "put in my cart", "add item to cart", "include this product",
    ],
    "VIEW_CART": [
        "show my cart", "open basket", "view items in cart", "check what’s in my cart",
    ],
    "CHECKOUT": [
        "go to checkout", "buy now", "proceed to payment", "place my order",
    ],
    "PRODUCT_INFO": [
        "tell me about this product", "details of this item", "show specs", "show me information",
    ],
    "COMPARE": [
        "compare this with another", "which is better", "show comparison", "compare two products",
    ],
    "FAQ": [
        "how to return item", "shipping policy", "refund details", "help me with an issue",
    ],
}

# --- Standalone test block ---
if __name__ == "__main__":
    matcher = EmbeddingMatcher()
    while True:
        user_query = input("🗣️  Query: ")
        if user_query.lower() == "exit":
            break
        results = matcher.search(user_query)
        if results:
            print(f"✅ {results[0]}")
        else:
            print("⚠️ No match found.")
