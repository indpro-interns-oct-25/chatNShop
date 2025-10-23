# app/ai/intent_classification/keyword_matcher.py
from typing import Dict, Any

# Very simple placeholder matcher; replace with your existing rules if you have them.
_KEYWORDS = {
    "search_product": ["search", "find", "look up", "show me", "looking for"],
    "add_to_cart": ["add to cart", "add this", "put in basket", "buy this"],
    "view_cart": ["show my cart", "open basket", "what's in my cart", "view cart"],
    "checkout": ["checkout", "buy now", "place the order", "proceed to checkout"],
    "greeting": ["hello", "hi", "hey", "good morning", "good evening"],
}

class KeywordMatcher:
    def match(self, text: str) -> Dict[str, Any]:
        t = text.lower()
        for intent, kws in _KEYWORDS.items():
            for kw in kws:
                if kw in t:
                    return {
                        "intent": intent,
                        "confidence": 0.85,
                        "method": "keyword",
                        "latency_ms": 0.1,
                    }
        return {"intent": None, "confidence": 0.0, "method": "keyword", "latency_ms": 0.1}
