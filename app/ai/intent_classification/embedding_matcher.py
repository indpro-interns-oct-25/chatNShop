"""
embedding_matcher.py
Implements pre-trained embedding-based semantic similarity matching for user intents.
Falls back to keyword-based matching if embedding confidence is low.
"""

import os
import time
import numpy as np
from sentence_transformers import SentenceTransformer, util

# -------------------------------------------------------------
# Load Pre-trained Embedding Model
# -------------------------------------------------------------
print("🔄 Loading model 'all-MiniLM-L6-v2'...")
start_time = time.time()

model = SentenceTransformer('all-MiniLM-L6-v2')

print(f"✅ EmbeddingMatcher ready. Model loaded in {time.time() - start_time:.2f}s")

# -------------------------------------------------------------
# Define Intents and Example Phrases
# -------------------------------------------------------------
intent_examples = {
    "SEARCH": [
        "find this item",
        "show me products",
        "search for shoes",
        "look up phone covers",
    ],
    "ADD_TO_CART": [
        "add this to my basket",
        "put in my cart",
        "add item to cart",
        "include this product",
    ],
    "VIEW_CART": [
        "show my cart",
        "open basket",
        "view items in cart",
        "check what’s in my cart",
    ],
    "CHECKOUT": [
        "go to checkout",
        "buy now",
        "proceed to payment",
        "place my order",
    ],
    "PRODUCT_INFO": [
        "tell me about this product",
        "details of this item",
        "show specs",
        "show me information",
    ],
    "COMPARE": [
        "compare this with another",
        "which is better",
        "show comparison",
        "compare two products",
    ],
    "FAQ": [
        "how to return item",
        "shipping policy",
        "refund details",
        "help me with an issue",
    ],
}

# -------------------------------------------------------------
# Precompute Reference Embeddings for Each Intent
# -------------------------------------------------------------
intent_embeddings = {}
for intent, phrases in intent_examples.items():
    intent_embeddings[intent] = model.encode(phrases, convert_to_tensor=True)

# -------------------------------------------------------------
# Fallback: Keyword Matcher Import (lazy import to avoid circulars)
# -------------------------------------------------------------
def keyword_fallback(user_query):
    """
    Tries keyword-based intent detection if embedding similarity is low.
    """
    try:
        from .keyword_matcher import keyword_match  # ensure this file exists
        kw_intent = keyword_match(user_query)
        if kw_intent:
            return kw_intent
        return None
    except Exception as e:
        print(f"⚠️ Keyword fallback failed: {e}")
        return None

# -------------------------------------------------------------
# Function: Match Intent (Hybrid)
# -------------------------------------------------------------
def match_intent(user_query, threshold=0.60):
    """
    Matches user query to the closest intent using embeddings.
    Falls back to keyword matching if confidence < threshold.
    Returns (intent, confidence, fallback_used)
    """
    try:
        query_emb = model.encode(user_query, convert_to_tensor=True)
        best_intent = None
        best_score = 0.0

        # Compute similarity across all intents
        for intent, ref_emb in intent_embeddings.items():
            sim = util.cos_sim(query_emb, ref_emb).max().item()
            if sim > best_score:
                best_score = sim
                best_intent = intent

        # High-confidence embedding match
        if best_score >= threshold:
            return best_intent, round(best_score, 3), False

        # Low confidence → Fallback to keyword matching
        kw_intent = keyword_fallback(user_query)
        if kw_intent:
            return kw_intent, round(best_score, 3), True

        # No confident match found
        return None, round(best_score, 3), True

    except Exception as e:
        print(f"❌ Error during intent matching: {e}")
        return None, 0.0, True

# -------------------------------------------------------------
# Test Block (for standalone execution)
# -------------------------------------------------------------
if __name__ == "__main__":
    print("\n🚀 Testing Semantic Intent Matching (with Fallback)...\n")

    while True:
        user_query = input("🗣️  User Query (or 'exit'): ").strip()
        if user_query.lower() == "exit":
            print("👋 Exiting matcher.")
            break

        start = time.time()
        intent, confidence, fallback = match_intent(user_query)
        latency = (time.time() - start) * 1000

        if intent:
            if fallback:
                print(f"🔁 Fallback used → Keyword Match: {intent} ({confidence})")
            else:
                print(f"✅ Semantic Match! ({confidence}) → {intent}")
        else:
            print(f"⚠️ No match found. Try rephrasing.")

        print(f"⏱️  Latency: {latency:.2f} ms\n")
