# tests/test_integration_intents.py
from app.ai.intent_classification.keyword_matcher import match_keywords
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher

def test_keyword_and_embedding_agree(sample_queries):
    matcher = EmbeddingMatcher()
    for query in sample_queries:
        kw = match_keywords(query)
        emb = matcher.search(query)
        assert isinstance(kw, list)
        assert isinstance(emb, list)
        assert kw or emb
