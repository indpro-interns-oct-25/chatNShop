# chatNShop/app/ai/intent_classification/intents.py

from app.ai.intent_classification.keyword_matcher import keyword_match
from app.ai.intent_classification.embedding_matcher import get_intent_from_embeddings

def classify_intent(user_query):
    """
    Hybrid intent classifier:
    1️⃣ Try keyword matching first
    2️⃣ Fallback to semantic embedding matching
    """
    print(f"\n🧠 Analysing user query: {user_query}")

    # 1️⃣ Keyword-based match
    intent = keyword_match(user_query)
    if intent and intent != "None":
        print(f"✅ Matched by Keyword: {intent}")
        return intent

    # 2️⃣ Semantic match fallback
    print("[🔍 Switching to Semantic Matching...]")
    intent = get_intent_from_embeddings(user_query)

    if intent and intent != "None":
        print(f"✅ Matched by Semantic Model: {intent}")
    else:
        print("❌ No intent match found.")

    return intent

# 🧪 Local test
if __name__ == "__main__":
    test_queries = [
        "add this item to my basket",
        "can I see my shopping cart?",
        "I want to check out now",
        "find me some shoes",
        "what is this item?",
        "compare these two products",
    ]

    for query in test_queries:
        classify_intent(query)
        print("-" * 60)
