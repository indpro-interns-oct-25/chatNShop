# chatNShop/app/ai/intent_classification/embedding_matcher.py

from sentence_transformers import SentenceTransformer, util

# 1️⃣ Load pre-trained model
print("🔄 Loading SentenceTransformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Model loaded successfully!\n")

# 2️⃣ Define intents with example phrases
INTENT_CATEGORIES = {
    "SEARCH": ["search for product", "find item", "look up product"],
    "ADD_TO_CART": ["add to cart", "buy this item", "put product in cart"],
    "VIEW_CART": ["show my cart", "open basket", "see what I added"],
    "CHECKOUT": ["checkout", "place my order", "buy now", "proceed to pay"],
    "PRODUCT_INFO": ["tell me about this product", "product details", "more info"],
    "COMPARE": ["compare", "compare these items", "difference between products"],
}

# 3️⃣ Precompute embeddings for each intent
intent_embeddings = {}
for intent, examples in INTENT_CATEGORIES.items():
    intent_embeddings[intent] = model.encode(examples, convert_to_tensor=True)

# 4️⃣ Similarity threshold
SIMILARITY_THRESHOLD = 0.45

def match_intent(user_input: str):
    """Returns the most semantically similar intent, or None."""
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
        print(f"[Fallback 🔁] No strong semantic match ({best_score:.2f})")
        return None

# 5️⃣ Provide a function for intents.py to import
def get_intent_from_embeddings(user_input):
    return match_intent(user_input)
