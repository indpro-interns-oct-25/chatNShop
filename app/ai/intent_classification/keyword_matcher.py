import json
import os
import re
import time
from collections import defaultdict

class KeywordMatcher:
    def __init__(self, keywords_dir):
        """
        Initialize matcher with path to keyword dictionary folder.
        Each JSON file should contain a mapping: { "INTENT_NAME": ["keyword1", "keyword2", ...] }
        """
        self.keywords_dir = keywords_dir
        self.keyword_data = {}
        self._load_keywords()

    def _load_keywords(self):
        """Load all keyword JSONs into memory"""
        for file_name in os.listdir(self.keywords_dir):
            if file_name.endswith(".json"):
                path = os.path.join(self.keywords_dir, file_name)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.keyword_data.update(data)

    def preprocess(self, text):
        """Normalize text (case-insensitive, remove special chars)"""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def match_intent(self, query):
        """
        Match query against loaded keyword sets.
        Returns: { 'action_code': str, 'confidence': float, 'matched_keywords': [list] }
        """
        start_time = time.time()
        processed_query = self.preprocess(query)
        query_words = set(processed_query.split())

        best_intent = None
        best_score = 0.0
        best_matches = []

        # Check all intents
        for intent, keywords in self.keyword_data.items():
            matched = []
            score = 0
            for kw in keywords:
                kw_proc = self.preprocess(kw)
                
                # ✅ Exact or partial match
                if kw_proc in processed_query or any(kw_word in query_words for kw_word in kw_proc.split()):
                    matched.append(kw)
                    score += 1

            if matched:
                # Normalize score between 0–1
                confidence = min(1.0, score / len(keywords))
                if confidence > best_score:
                    best_score = confidence
                    best_intent = intent
                    best_matches = matched

        elapsed = (time.time() - start_time) * 1000  # in ms

        return {
            "action_code": best_intent if best_intent else "NO_MATCH",
            "confidence": round(best_score, 3),
            "matched_keywords": best_matches,
            "response_time_ms": round(elapsed, 2)
        }

# For direct test
if __name__ == "__main__":
    matcher = KeywordMatcher(keywords_dir="app/ai/intent_classification/keywords")

    queries = [
        "I want to track my order",
        "cancel my return",
        "change delivery date",
        "apply discount coupon",
        "lock my account"
    ]

    for q in queries:
        print("\nQuery:", q)
        print(matcher.match_intent(q))
