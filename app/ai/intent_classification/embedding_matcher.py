"""
embedding_matcher.py
Implements pre-trained embedding-based semantic similarity matching for user intents.
"""

import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any

# --- THIS IS THE FIX ---
from app.ai.intent_classification.keyword_matcher import match_keywords
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
        Returns a list of all intents and their scores.
        """
        try:
            query_emb = self.model.encode(query, convert_to_tensor=True)
            results = []

            # Compute similarity across all intents
            for intent, ref_emb in self.intent_embeddings.items():
                sim = util.cos_sim(query_emb, ref_emb).max().item()
                results.append({
                    "id": intent, 
                    "intent": intent,
                    "score": round(sim, 4),
                    "source": "embedding"
                })

            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            return results

        except Exception as e:
            print(f"❌ Error during embedding matching: {e}")
            return []

# -------------------------------------------------------------
# (All of your original data/functions remain below)
# -------------------------------------------------------------

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

# -------------------------------------------------------------
# Standalone Test Block (for running this file directly)
# -------------------------------------------------------------

def keyword_fallback_test(user_query):
    """
    (For standalone testing only)
    """
    try:
        kw_results = match_keywords(user_query, top_n=1)
        if kw_results:
            return kw_results[0].get("intent")
        return None
    except Exception as e:
        print(f"⚠️ Keyword fallback test failed: {e}")
        return None

if __name__ == "__main__":
    print("\n🚀 Testing Embedding Matcher (standalone)...\n")
    
    matcher = EmbeddingMatcher()
    
    while True:
        user_query = input("🗣️  User Query (or 'exit'): ").strip()
        if user_query.lower() == "exit":
            print("👋 Exiting matcher.")
            break

        start = time.time()
        search_results = matcher.search(user_query)
        latency = (time.time() - start) * 1000

        if search_results:
            print(f"✅ Top Match: {search_results[0]['intent']} (Score: {search_results[0]['score']:.4f})")
            
            if search_results[0]['score'] < 0.6:
                print("--- Low confidence, testing keyword fallback ---")
                kw_intent = keyword_fallback_test(user_query)
                if kw_intent:
                    print(f"🔁 Fallback found: {kw_intent}")
                else:
                    print("... Fallback found no match.")
        else:
            print(f"⚠️ No match found.")

        print(f"⏱️  Latency: {latency:.2f} ms\n")