import os
import json
import logging
from typing import Dict, Any, List
from app.ai.intent_classification.keywords.loader import load_all_keywords
from app.utils.text_processing import normalize_text

logger = logging.getLogger(__name__)

KEYWORDS_DIR = os.path.join(os.path.dirname(__file__), "keywords")


class KeywordMatcher:
    def __init__(self):
        self.keywords = load_all_keywords(KEYWORDS_DIR)
        logger.info("✅ KeywordMatcher initialized and keywords loaded.")

    def match(self, text: str) -> Dict[str, Any]:
        """
        Match input text against known intent keywords.
        Returns structured result instead of raw list.
        """
        text = normalize_text(text)
        matches: List[Dict[str, Any]] = []

        for intent, kw_list in self.keywords.items():
            for kw in kw_list:
                if kw in text:
                    matches.append({
                        "intent": intent,
                        "keyword": kw,
                        "confidence": 0.9
                    })

        # ✅ If matches found → return the best one
        if matches:
            best_match = max(matches, key=lambda x: x["confidence"])
            logger.info(f"✅ Keyword match found: {best_match}")
            return best_match

        # ⚠️ No match
        logger.warning("⚠️ No keyword match found.")
        return {"intent": "UNKNOWN", "confidence": 0.0, "keyword": None}


if __name__ == "__main__":
    matcher = KeywordMatcher()
    sample_queries = [
        "show me red nike shoes",
        "add this to my cart",
        "what is the price of apple watch",
        "find blue jeans under 2000",
        "checkout my order"
    ]

    for q in sample_queries:
        print(f"\n🧾 Query: {q}")
        print("Result:", matcher.match(q))
