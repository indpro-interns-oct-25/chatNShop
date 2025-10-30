# tests/test_performance.py
import time
from app.ai.intent_classification.keyword_matcher import match_keywords

def test_keyword_match_performance():
    text = "Add to cart this product please"
    start = time.time()
    for _ in range(1000):
        match_keywords(text)
    elapsed = time.time() - start
    assert elapsed < 2.0  # should handle 1000 queries in <2s
