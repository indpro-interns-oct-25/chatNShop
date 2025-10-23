# tests/test_ai/test_intent_classification/test_embedding_matcher.py
import time
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher
from app.ai.intent_classification.intents import INTENT_REFERENCES

def test_basic_match_and_latency():
    matcher = EmbeddingMatcher.build_singleton(INTENT_REFERENCES)
    _ = matcher.match("hello there")  # warm-up
    t0 = time.perf_counter()
    r = matcher.match("hi, good morning")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert r.intent in {"greeting", None}
    assert elapsed_ms < 100.0
