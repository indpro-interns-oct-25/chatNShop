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
try:
    from app.ai.intent_classification.intents_modular.definitions import ALL_INTENT_DEFINITIONS  # type: ignore
except Exception:
    ALL_INTENT_DEFINITIONS = None  # type: ignore
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
        
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.intent_examples = self._load_reference_phrases()
        self.intent_embeddings = self._precompute_embeddings()
        # Simple in-memory cache for recent query embeddings
        self._query_cache: Dict[str, Any] = {}
        self._query_cache_max = 512
        
        print(f"✅ EmbeddingMatcher ready. Model loaded in {time.time() - start_time:.2f}s")

    def _load_reference_phrases(self) -> Dict[str, List[str]]:
        """Build mapping of action_code -> example_phrases from taxonomy; fallback to INTENT_EXAMPLES."""
        if ALL_INTENT_DEFINITIONS:
            refs: Dict[str, List[str]] = {}
            try:
                for _name, definition in ALL_INTENT_DEFINITIONS.items():  # type: ignore
                    action = getattr(definition, "action_code", None)
                    phrases = getattr(definition, "example_phrases", None)
                    if not action or not phrases:
                        continue
                    # Normalize enum to its name for exact action_code match
                    if hasattr(action, "name"):
                        action_str = getattr(action, "name")
                    elif isinstance(action, str):
                        action_str = action
                    else:
                        action_str = str(action)
                    if isinstance(phrases, list) and phrases:
                        seen = set()
                        norm: List[str] = []
                        for p in phrases:
                            if isinstance(p, str):
                                k = p.strip()
                                if k and k not in seen:
                                    seen.add(k)
                                    norm.append(k)
                        if norm:
                            refs[action_str] = norm
                if refs:
                    print(f"🔗 Embedding references loaded from taxonomy: {len(refs)} action codes")
                    return refs
            except Exception:
                pass
        print("⚠️ Falling back to built-in INTENT_EXAMPLES for embedding references")
        return INTENT_EXAMPLES

    def _precompute_embeddings(self) -> Dict[str, Any]:
        """Pre-computes and caches the embeddings for all example phrases."""
        embeddings: Dict[str, Any] = {}
        for action_code, phrases in self.intent_examples.items():
            try:
                embeddings[action_code] = self.model.encode(phrases, convert_to_tensor=True)
            except Exception:
                continue
        return embeddings

    def _encode_query_cached(self, query: str):
        """Encode query with a small LRU-like cache to avoid repeated work."""
        key = query.strip().lower()
        emb = self._query_cache.get(key)
        if emb is not None:
            return emb
        emb = self.model.encode(key, convert_to_tensor=True)
        # Naive size control
        if len(self._query_cache) >= self._query_cache_max:
            # drop an arbitrary item (FIFO-like behavior)
            try:
                self._query_cache.pop(next(iter(self._query_cache)))
            except Exception:
                self._query_cache.clear()
        self._query_cache[key] = emb
        return emb

    def search(self, query: str, threshold: float = 0.60) -> List[Dict]:
        """
        Matches user query to the closest intent using embeddings.
        Returns a list of all intents and their scores with enhanced error handling.
        """
        try:
            # Enhanced query preprocessing
            if not query or not query.strip():
                return []
            
            # Clean and normalize query
            clean_query = query.strip().lower()
            if len(clean_query) < 2:  # Too short to be meaningful
                return []
            
            query_emb = self._encode_query_cached(clean_query)
            results = []

            # Compute similarity across all action codes
            for action_code, ref_emb in self.intent_embeddings.items():
                if ref_emb is not None:
                    sim = util.cos_sim(query_emb, ref_emb).max().item()
                    # Only include results above minimum threshold
                    if sim >= 0.1:  # Very low threshold to catch edge cases
                        results.append({
                            "id": action_code, 
                            "intent": action_code,
                            "score": round(sim, 4),
                            "source": "embedding",
                            "query": clean_query
                        })

            # Sort by score
            results.sort(key=lambda x: x['score'], reverse=True)
            return results

        except Exception as e:
            print(f"❌ Error during embedding matching: {e}")
            # Return a generic search result as fallback
            return [{
                "id": "SEARCH_PRODUCT",
                "intent": "SEARCH_PRODUCT", 
                "score": 0.1,
                "source": "embedding_fallback",
                "error": str(e)
            }]

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