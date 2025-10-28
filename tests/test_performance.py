# tests/test_performance.py
import time
import pytest
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

QUERIES = [
    "checkout", "add to cart", "apply coupon", "view cart", "redeem gift card",
    "track my order", "change my shipping address", "remove item", "show me bestsellers", "how much is this"
]
QUERIES = (QUERIES * 100)[:1000]  # 1000 queries

@pytest.mark.perf
@pytest.mark.slow
def test_1000_queries_throughput(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    start = time.perf_counter()
    for q in QUERIES:
        _ = m.match_intent(q)
    duration = time.perf_counter() - start
    avg_ms = (duration / len(QUERIES)) * 1000.0
    # Relaxed threshold for local dev; tune to 50ms on faster infra
    assert avg_ms < 200.0, f"Avg per-query too slow: {avg_ms:.2f}ms"
