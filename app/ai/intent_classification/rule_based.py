# A simple weighted keyword recognizer
INTENT_WEIGHTS = {
    "search_product": {
        "search": 8, "find": 8, "look for": 7, "show me": 6, "browse": 5,
        "i need": 3, "i want": 3, "t-shirt": 4, "shoes": 4, "headphones": 4,
        "wallet": 4, "mug": 4, "running": 4, "coffee": 4
    },
    "order_status": {
        "track": 10, "where is my order": 10, "order status": 10,
        "delivery": 7, "package": 7, "shipped": 6
    },
    "add_to_cart": {
        "add to cart": 10, "put in cart": 10, "add to basket": 10,
        "buy this": 8, "i'll take it": 8, "add this": 7
    }
}

def get_intent_rule_based(query: str) -> str:
    query = query.lower()
    scores = {
        "search_product": 0,
        "order_status": 0,
        "add_to_cart": 0
    }

    for intent, keywords in INTENT_WEIGHTS.items():
        for keyword, weight in keywords.items():
            if keyword in query:
                scores[intent] += weight

    # Find the intent with the highest score
    best_intent = max(scores, key=scores.get)

    # Only return a specific intent if it has a score > 0
    if scores[best_intent] > 0:
        return best_intent

    # Default fallback intent
    return "search_product"