# tests/test_keyword_matcher_unit.py
from app.ai.intent_classification.keyword_matcher import match_keywords

def test_exact_match():
    result = match_keywords("add to cart")
    assert result
    assert result[0]["intent"] == "ADD_TO_CART"

def test_partial_match():
    result = match_keywords("add this item")
    assert any("ADD_TO_CART" in r["intent"] for r in result)

def test_no_match():
    result = match_keywords("nonsense gibberish")
    assert result == []

def test_special_chars():
    result = match_keywords("Add-to-cart!!!")
    assert result and result[0]["intent"] == "ADD_TO_CART"

def test_case_insensitive():
    r1 = match_keywords("Add To Cart")
    r2 = match_keywords("add to cart")
    assert r1[0]["intent"] == r2[0]["intent"]
