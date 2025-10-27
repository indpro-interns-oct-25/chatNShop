# app/ai/intent_classification/keyword_matcher.py

"""
Simple keyword-based intent matcher.
Used as fallback if embedding similarity is low.
"""

# Map keywords/phrases to intent codes
KEYWORD_INTENT_MAP = {
    "add to cart": "add_to_cart",
    "buy this item": "add_to_cart",
    "put product in cart": "add_to_cart",
    "view cart": "view_cart",
    "show my cart": "view_cart",
    "open basket": "view_cart",
    "checkout": "checkout",
    "place my order": "checkout",
    "buy now": "checkout",
    "proceed to pay": "checkout",
    "product info": "product_info",
    "tell me about this product": "product_info",
    "product details": "product_info",
    "more info": "product_info",
    "search": "search_product",
    "find item": "search_product",
    "look up product": "search_product",
    "compare": "compare",
    "difference": "compare",
}

def match(user_query: str):
    """
    Return the intent from keyword mapping if found, else None.
    """
    user_query_lower = user_query.lower()
    for keyword, intent in KEYWORD_INTENT_MAP.items():
        if keyword in user_query_lower:
            return intent
    return None

