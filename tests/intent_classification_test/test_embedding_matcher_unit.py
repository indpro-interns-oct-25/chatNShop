# tests/test_embedding_matcher_unit.py
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher

def test_model_loads():
    matcher = EmbeddingMatcher()
    assert matcher.model is not None

def test_basic_search():
    matcher = EmbeddingMatcher()
    results = matcher.search("find shoes")
    assert any("SEARCH" in r["intent"] for r in results)

def test_empty_query():
    matcher = EmbeddingMatcher()
    assert matcher.search("") == []

def test_low_confidence_fallback():
    matcher = EmbeddingMatcher()
    results = matcher.search("abcd1234")
    assert isinstance(results, list)
