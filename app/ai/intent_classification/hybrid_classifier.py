# app/ai/intent_classification/hybrid_classifier.py

import re

class HybridIntentClassifier:
    """
    Hybrid Intent Classifier:
    Combines simple keyword + pattern rules with entity extraction.
    Later you can plug in an LLM model or vector search if needed.
    """

    def __init__(self):
        self.intent_keywords = {
            "search": ["show", "find", "buy", "looking for", "search", "need"],
            "cancel": ["cancel", "stop", "abort"],
            "track": ["track", "status", "order"],
            "greeting": ["hi", "hello", "hey"]
        }

    def classify(self, text: str):
        text_lower = text.lower()

        # ----- Intent Detection -----
        intent = "unknown"
        confidence = 0.5
        for key, words in self.intent_keywords.items():
            if any(w in text_lower for w in words):
                intent = key.upper()
                confidence = 0.9
                break

        # ----- Entity Extraction -----
        entities = self.extract_entities(text_lower)

        # ----- Fake Search Results -----
        search_results = []
        if intent == "SEARCH" and entities.get("product_name"):
            search_results = [
                {
                    "product_name": f"{entities.get('brand', '').title()} {entities['product_name'].title()}",
                    "brand": entities.get("brand"),
                    "price": 2999,
                    "color": entities.get("color")
                }
            ]

        return {
            "action_code": intent,
            "confidence": confidence,
            "entities": entities,
            "search_results": search_results,
            "original_text": text
        }

    def extract_entities(self, text: str):
        """Extracts structured entities like brand, color, price, etc."""
        brand_list = ["nike", "puma", "adidas", "reebok", "apple", "samsung"]
        colors = ["red", "blue", "black", "white", "green", "yellow"]

        brand = next((b for b in brand_list if b in text), None)
        color = next((c for c in colors if c in text), None)
        price_match = re.search(r"(\d{3,6})", text)
        price = float(price_match.group(1)) if price_match else None

        entities = {
            "product_name": self.detect_product(text),
            "brand": brand,
            "color": color,
            "size": self.detect_size(text),
            "price_range": {"min": None, "max": price, "currency": "INR"} if price else None,
            "category": self.detect_category(text)
        }

        return entities

    def detect_product(self, text: str):
        words = ["shoe", "shoes", "tshirt", "shirt", "phone", "laptop", "watch", "bag"]
        for w in words:
            if w in text:
                return w
        return None

    def detect_category(self, text: str):
        if "electronics" in text or "phone" in text or "laptop" in text:
            return "Electronics"
        if "shoe" in text or "shirt" in text or "tshirt" in text:
            return "Fashion"
        return None

    def detect_size(self, text: str):
        size_match = re.search(r"\b(size\s*\d{1,2})\b", text)
        return size_match.group(1) if size_match else None
