# app/ai/intent_classification/rule_based.py

"""
Rule-Based Intent Classifier
Simple keyword matching for chatNShop intents
"""

from typing import Optional, Dict

# Final intent keywords dictionary
INTENT_KEYWORDS = {
    "buy_product": [
        "buy", "purchase", "order", "get", "acquire", "grab", "shop", "procure", "pick up",
        "purchase online", "purchase now", "buy now", "shop online", "get me", "want to buy",
        "looking for", "add to cart", "checkout", "pay for", "purchase item", "buy item",
        "get item", "order now", "buying", "purchasing", "shopping", "grab it", "order this",
        "get this", "purchase this", "want it", "need it", "buy ASAP", "buy today", "add to basket",
        "procure item", "checkout now", "buy product", "get product", "order product", "purchase product",
        "want product", "looking to buy", "add to cart now", "buy online", "shop now", "grab online",
        "purchase quickly", "get online", "order online", "checkout product", "get it now", "buy it now",
        "buy this item", "purchase this item", "shop this item", "want to order", "need to buy", "grab this",
        "procure now", "purchase fast", "buy fast", "get fast", "want it fast", "order today", "shop today"
    ],
    "track_order": [
        "track", "status", "delivery", "where is", "order update", "shipping", "shipment",
        "track my order", "track package", "order location", "delivery status", "check order",
        "track shipment", "track delivery", "order tracking", "order info", "package status",
        "order progress", "shipment status", "track item", "order details", "where is my order",
        "track my package", "delivery info", "track parcel", "order whereabouts", "check delivery",
        "shipping info", "track shipment status", "package tracking", "track my item", "order shipment",
        "track order online", "order tracking info", "shipment details", "delivery update", "track order status",
        "parcel status", "track my shipment", "where's my order", "order position", "track delivery info", "check parcel",
        "tracking details", "track delivery status", "package location", "find my order", "track order now",
        "order shipment info", "shipping status", "track my order online", "delivery tracking", "shipment tracking"
    ],
    "return_product": [
        "return", "refund", "replace", "send back", "exchange", "want my money back", "unsatisfied",
        "wrong product", "damaged", "defective", "cancel delivery", "return order", "refund order",
        "replace item", "exchange product", "return item", "need refund", "item wrong", "item damaged",
        "send it back", "want replacement", "replace now", "return now", "refund request", "unsatisfied product",
        "return product", "exchange item", "wrong item", "defective item", "replace damaged", "return damaged",
        "return defective", "refund my money", "get refund", "return purchased item", "return order online",
        "exchange purchased product", "return faulty item", "replace wrong item", "return wrong product", "refund item",
        "send product back", "exchange faulty product", "return damaged product", "item not good", "return immediately",
        "replace immediately", "refund immediately", "return wrong order", "refund wrong order", "exchange order",
        "return parcel", "refund parcel", "replace parcel", "return shipped item", "refund shipped item"
    ],
    "cancel_order": [
        "cancel order", "stop order", "abort order", "call off", "order cancellation", "stop delivery",
        "halt order", "terminate order", "cancel purchase", "cancel shipment", "cancel item", "undo order",
        "revoke order", "remove order", "discard order", "cancel online order", "cancel order now", "cancel this order",
        "stop this order", "abort this order", "cancel current order", "terminate purchase", "cancel checkout",
        "cancel transaction", "stop purchase", "revoke purchase", "cancel buying", "cancel order immediately",
        "halt shipment", "call off purchase", "undo purchase", "remove item", "stop order online", "cancel product",
        "cancel delivery", "cancel order request", "abort purchase", "terminate item", "stop delivery now", "cancel item purchase"
    ],
    "greet": [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "morning", "afternoon",
        "evening", "hiya", "greetings", "yo", "what's up", "howdy", "sup", "hi there", "hey there", "hello there",
        "hiya friend", "hey friend", "morning!", "afternoon!", "evening!", "hi!", "hello!", "hey!", "hello friend",
        "hi buddy", "hey buddy", "morning mate", "afternoon mate", "evening mate", "hi mate", "hello mate",
        "hey mate", "hiya mate", "greetings friend", "what's happening", "how's it going", "good day", "hello friend!",
        "hi there!", "hey there!", "greetings!", "yo friend", "hiya buddy", "hey buddy!", "hi buddy!"
    ],
    "goodbye": [
        "bye", "goodbye", "see you", "see ya", "farewell", "take care", "catch you later", "later", "talk later",
        "see you soon", "see you later", "bye bye", "see you around", "adios", "ciao", "cheerio", "ta ta",
        "bye now", "good night", "night", "goodbye friend", "bye friend", "see ya friend", "see ya later friend",
        "catch you soon", "farewell friend", "good night friend", "bye bye friend", "see you soon friend", "bye now friend",
        "goodbye mate", "see ya mate", "bye mate", "catch you later mate", "later mate", "good night mate", "ta ta mate",
        "see you around mate", "ciao mate", "adios mate", "goodbye buddy", "bye buddy", "see ya buddy", "later buddy",
        "good night buddy", "bye bye buddy", "farewell buddy", "see you soon buddy", "ta ta buddy", "ciao buddy"
    ],
    "ask_discount": [
        "discount", "offer", "sale", "deal", "promo", "promotion", "coupon", "voucher", "rebate",
        "price cut", "special offer", "clearance", "bargain", "price reduction", "cheaper", "discounted",
        "cheap", "flash sale", "limited offer", "sale today", "discount today", "offer today", "promotion today",
        "voucher today", "rebate today", "coupon today", "price slash", "hot deal", "special discount",
        "clearance sale", "deal today", "discounted price", "bargain offer", "cheap deal", "limited time offer",
        "promo code", "coupon code", "sale online", "discount online", "online offer", "flash discount",
        "daily deal", "mega sale", "super sale", "offer online", "discount coupon", "buy one get one",
        "bogo", "buy one get one free", "limited offer today", "deal now", "sale now", "special offer today"
    ]
}


# ---------------------------
# Rule-Based Classification Function
# ---------------------------
def classify_intent_rule_based(text: str) -> Dict:
    """
    Classify intent based on keywords dictionary.
    Returns a dict with intent, confidence, method.
    """
    text_lower = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return {
                    "intent": intent,
                    "confidence": 0.9,  # fixed confidence for rule-based
                    "method": "rule-based"
                }
    return {
        "intent": "unknown",
        "confidence": 0.0,
        "method": "rule-based"
    }

# ---------------------------
# Test run
# ---------------------------
if __name__ == "__main__":
    test_texts = [
        "I want to buy a laptop",
        "Can you track my order?",
        "Hello there!",
        "Do you have any discount today?",
        "I want to cancel my order",
        "Bye!"
    ]

    for text in test_texts:
        print(text, "=>", classify_intent_rule_based(text))