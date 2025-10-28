# tests/test_edge_cases.py
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

def test_empty_query(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    out = m.match_intent("")
    assert isinstance(out, dict)
    assert "action_code" in out

def test_special_chars_only(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    q = "!@#$%^&*()_+{}:\"<>?~`"
    out = m.match_intent(q)
    assert isinstance(out, dict)

def test_very_long_query(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    q = "add to cart " * 5000
    out = m.match_intent(q)
    assert isinstance(out, dict)
