# chatNShop/app/ai/intent_classification/keyword_matcher.py

# Dictionary mapping keywords to intents
keyword_intent_map = {
    "add to cart": "ADD_TO_CART",
    "buy this item": "ADD_TO_CART",
    "put product in cart": "ADD_TO_CART",
    "view cart": "VIEW_CART",
    "show my cart": "VIEW_CART",
    "open basket": "VIEW_CART",
    "checkout": "CHECKOUT",
    "place my order": "CHECKOUT",
    "buy now": "CHECKOUT",
    "proceed to pay": "CHECKOUT",
    "product info": "PRODUCT_INFO",
    "tell me about this product": "PRODUCT_INFO",
    "product details": "PRODUCT_INFO",
    "more info": "PRODUCT_INFO",
    "search": "SEARCH",
    "find item": "SEARCH",
    "look up product": "SEARCH",
    "compare": "COMPARE",
}

def keyword_match(user_query):
    """
    Check if any keyword exists in the user query.
    Returns the intent code if found, else "None".
    """
    user_query_lower = user_query.lower()
    for keyword, intent in keyword_intent_map.items():
        if keyword in user_query_lower:
            return intent
    return "None"
