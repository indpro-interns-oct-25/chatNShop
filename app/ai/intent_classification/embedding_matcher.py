from sentence_transformers import SentenceTransformer, util

# ✅ 1. Load Pre-trained Model (semantic embeddings)
print("🔄 Loading SentenceTransformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Model loaded successfully!\n")

# ✅ 2. Define Intent Categories
INTENT_CATEGORIES = {
    "SEARCH": ["search for product", "find item", "look up product"],
    "ADD_TO_CART": ["add to cart", "buy this item", "put product in cart"],
    "VIEW_CART": ["show my cart", "open basket", "see what I added"],
    "CHECKOUT": ["checkout", "place my order", "buy now", "proceed to pay"],
    "PRODUCT_INFO": ["tell me about this product", "product details", "more info"],
}

# ✅ 3. Precompute embeddings for all reference phrases
intent_embeddings = {}
for intent, examples in INTENT_CATEGORIES.items():
    intent_embeddings[intent] = model.encode(examples, convert_to_tensor=True)

# ✅ 4. Define a similarity threshold
SIMILARITY_THRESHOLD = 0.60  # You can tune this later


def match_intent(user_input: str):
    """Returns the most semantically similar intent, or fallback."""
    user_emb = model.encode(user_input, convert_to_tensor=True)

    best_intent = None
    best_score = 0.0

    for intent, embeddings in intent_embeddings.items():
        similarity = util.cos_sim(user_emb, embeddings).max().item()
        if similarity > best_score:
            best_score = similarity
            best_intent = intent

    if best_score >= SIMILARITY_THRESHOLD:
        print(f"✅ Successful Semantic Match! ({best_score:.2f}) → {best_intent}")
        return best_intent
    else:
        print(f"[Fallback 🔁] No strong semantic match ({best_score:.2f}), fallback to keyword.")
        print("✅ Final Matched Intent → None\n")
        return None


# ✅ 5. TEST EXAMPLES
if __name__ == "__main__":
    print("🚀 Testing Semantic Intent Matching...\n")

    test_queries = [
        "add this item to my basket",
        "can I see my shopping cart?",
        "I want to check out now",
        "find me some shoes",
        "what is this item?",
    ]

    for query in test_queries:
        print(f"🗣️ User Query: {query}")
        match_intent(query)
        print("-" * 60)
