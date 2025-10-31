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
<<<<<<< HEAD
from app.ai.llm_intent.qdrant_cache import store_vector
=======
try:
    from app.ai.intent_classification.intents_modular.definitions import ALL_INTENT_DEFINITIONS  # type: ignore
except Exception:
    ALL_INTENT_DEFINITIONS = None  # type: ignore
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b
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
<<<<<<< HEAD

=======
        
        self.model_name = model_name
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b
        self.model = SentenceTransformer(model_name)
        self.intent_examples = self._load_reference_phrases()
        self.intent_embeddings = self._precompute_embeddings()
<<<<<<< HEAD

=======
        # Simple in-memory cache for recent query embeddings
        self._query_cache: Dict[str, Any] = {}
        self._query_cache_max = 512
        
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b
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
        Includes Qdrant storage for analytics and caching.
        """
        try:
            if not query or not query.strip():
                return []

            clean_query = query.strip().lower()
            if len(clean_query) < 2:
                return []
<<<<<<< HEAD

            query_emb = self.model.encode(clean_query, convert_to_tensor=True)
            results = []

            # Compute similarity across intents
            for intent, ref_emb in self.intent_embeddings.items():
=======
            
            query_emb = self._encode_query_cached(clean_query)
            results = []

            # Compute similarity across all action codes
            for action_code, ref_emb in self.intent_embeddings.items():
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b
                if ref_emb is not None:
                    sim = util.cos_sim(query_emb, ref_emb).max().item()
                    if sim >= 0.1:
                        results.append({
<<<<<<< HEAD
                            "id": intent,
                            "intent": intent,
=======
                            "id": action_code, 
                            "intent": action_code,
>>>>>>> da921c5f57fe9bded2d8dbac52a4ed6c262dae0b
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
