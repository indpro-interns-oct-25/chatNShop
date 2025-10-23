# app/ai/intent_classification/embedding_matcher.py

"""
Embedding-based intent matcher with keyword fallback, caching, and latency logging.
"""

import os
import json
import time
import numpy as np
from sentence_transformers import SentenceTransformer

from .intents import INTENTS
from .keyword_matcher import match as keyword_match

# -------------------------
# Configuration
# -------------------------
MODEL_NAME = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.80
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "intent_embeddings.json")

# -------------------------
# Embedding Matcher Class
# -------------------------
class EmbeddingMatcher:
    def __init__(self):
        print(f"🔄 Loading model '{MODEL_NAME}'...")
        self.model = SentenceTransformer(MODEL_NAME)
        self.intent_embeddings = self._load_or_build_cache()
        print(f"✅ EmbeddingMatcher ready. {len(self.intent_embeddings)} intents loaded.\n")

    def _load_or_build_cache(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        # Load cache if exists
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {k: np.array(v) for k, v in data.items()}
            except Exception:
                print("⚠️ Failed to load cache, rebuilding...")

        # Build cache
        print("📦 Building intent embeddings from INTENTS...")
        embeddings = {}
        for intent, phrases in INTENTS.items():
            if not phrases:
                continue
            vecs = self.model.encode(phrases, show_progress_bar=False)
            embeddings[intent] = np.mean(vecs, axis=0).tolist()
        # Save cache
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(embeddings, f)
            print(f"💾 Saved cache to {CACHE_FILE}")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
        return {k: np.array(v) for k, v in embeddings.items()}

    @staticmethod
    def _cosine_similarity(a, b):
        a = np.array(a)
        b = np.array(b)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / denom) if denom != 0 else 0.0

    def predict(self, query: str):
        start_time = time.time()
        query = str(query).strip() if query else ""
        if query == "":
            return {"query": query, "predicted_intent": None, "confidence": 0.0, "fallback": False, "latency_ms": 0.0}

        query_emb = self.model.encode([query], show_progress_bar=False)[0]

        # Embedding match
        best_intent = None
        best_score = -1.0
        for intent, emb in self.intent_embeddings.items():
            score = self._cosine_similarity(query_emb, emb)
            if score > best_score:
                best_score = score
                best_intent = intent

        predicted = best_intent if best_score >= SIMILARITY_THRESHOLD else None
        fallback_used = False

        # Fallback to keyword match
        if predicted is None:
            kw_intent = keyword_match(query)
            if kw_intent:
                predicted = kw_intent
                fallback_used = True

        latency = (time.time() - start_time) * 1000.0
        return {
            "query": query,
            "predicted_intent": predicted,
            "confidence": round(float(best_score), 4),
            "fallback": fallback_used,
            "latency_ms": round(latency, 2)
        }

# -------------------------
# Demo
# -------------------------
if __name__ == "__main__":
    matcher = EmbeddingMatcher()
    test_queries = [
        "add this item to my basket",
        "can I see my shopping cart?",
        "I want to check out now",
        "find me some shoes",
        "what is this item?",
        "compare these two products",
        "search for red sneakers",
        "please add it to the bag"
    ]

    for q in test_queries:
        res = matcher.predict(q)
        print(f"Query: '{res['query']}' → Intent: {res['predicted_intent']}, "
              f"Confidence: {res['confidence']}, Fallback: {res['fallback']}, "
              f"Latency: {res['latency_ms']}ms")