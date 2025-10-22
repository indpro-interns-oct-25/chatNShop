import re

from app.ai.intent_classification.keyword_matcher import match_keywords


def test_exact_match():
    res = match_keywords("Add to cart")
    assert res
    assert res[0]["intent"] == "cart_add"
    assert res[0]["action"] == "ADD_TO_CART"
    assert res[0]["match_type"] == "exact"


def test_partial_match():
    res = match_keywords("I want to buy a phone")
    assert res
    # should match search_product partial 'buy {product}' pattern
    intents = [r["intent"] for r in res]
    assert "search_product" in intents


def test_regex_match():
    res = match_keywords("search for laptop")
    assert res
    # regex pattern defined for search_keywords should match
    found = False
    for r in res:
        if r["action"] == "SEARCH_PRODUCT_REGEX":
            found = True
    assert found
