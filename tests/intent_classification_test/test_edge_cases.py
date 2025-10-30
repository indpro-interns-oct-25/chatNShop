# tests/test_edge_cases.py
from app.ai.intent_classification.keyword_matcher import match_keywords

def test_empty_input():
    assert match_keywords("") == []

def test_very_long_input():
    text = "add to cart " * 1000
    res = match_keywords(text)
    assert res

def test_special_symbols():
    res = match_keywords("add#####to#cart$")
    assert res
