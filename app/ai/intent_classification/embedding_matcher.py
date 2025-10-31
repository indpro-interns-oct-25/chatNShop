import logging
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
    def __init__(self, client=None):
        """
        EmbeddingMatcher handles semantic similarity searches.
        :param client: Optional vector database client (e.g., QdrantClient)
        """
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def search(self, query_vector, collection_name="intents", top_k=5):
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
        Perform semantic search using the vector database client.
        Returns a list of matches with their similarity scores.
        """
        if not self.client:
            self.logger.warning("⚠️ No vector DB client provided; returning mock search results.")
            # Mock search result for development
            return [
                {
                    "payload": {"intent": "SEARCH_PRODUCT"},
                    "score": 0.95
                }
            ]
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

        try:
            response = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            return response
        except Exception as e:
            self.logger.error(f"❌ Error during vector search: {e}")
            return []

    def match_intent(self, query_vector, collection_name="intents", threshold=0.7):
        """
        Finds the best matching intent for a given query vector.
        :param query_vector: Embedding vector of the query text
        :param collection_name: Name of the vector collection
        :param threshold: Minimum similarity score for a valid match
        :return: Dict with 'intent' and 'score' or None
        """
        results = self.search(query_vector, collection_name=collection_name, top_k=5)
        if not results:
            self.logger.warning("No matching results found.")
            return None

        # Handle both mock and Qdrant response formats
        best_match = max(results, key=lambda r: r["score"] if isinstance(r, dict) else r.score)
        score = best_match["score"] if isinstance(best_match, dict) else best_match.score
        intent = (
            best_match["payload"]["intent"]
            if isinstance(best_match, dict)
            else best_match.payload.get("intent", "unknown")
        )

        if score >= threshold:
            return {
                "intent": intent,
                "score": round(score, 3)
            }

        self.logger.info("🟡 No intent exceeded threshold confidence.")
        return None
