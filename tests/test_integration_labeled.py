# tests/test_integration_labeled.py
import pytest
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

# Build synthetic labeled samples (100) — replace with real CSV later if available
SAMPLES = []
def add_samples(intent, phrases):
    for p in phrases:
        SAMPLES.append((p, intent))

add_samples("SEARCH_PRODUCT", [
    "search product", "find product", "look for product", "product search",
    "i want to find shoes", "show me black shoes", "find laptops", "where can i buy a phone",
    "search for running shoes", "look up headphones"
])

add_samples("ADD_TO_CART", [
    "add to cart", "put this in my cart", "add item", "buy now", "add to basket",
    "add product to cart", "please add this", "can you add it to cart", "include in cart", "save to cart"
])

add_samples("PRODUCT_INFO", [
    "product info", "tell me about this", "product details", "what is this", "show details",
    "product specifications", "specs", "more about this product", "product overview", "give details"
])

add_samples("VIEW_CART", [
    "view cart", "show my cart", "open cart", "what's in my cart", "display cart items",
    "see cart", "check my cart", "cart page", "view shopping cart", "look at cart"
])

# repeat / trim to 100
SAMPLES = (SAMPLES * 25)[:100]

@pytest.mark.parametrize("query,expected", SAMPLES)
def test_integration_queries(tmp_keywords_dir, query, expected):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    out = m.match_intent(query)
    assert "action_code" in out
    assert "confidence" in out
    assert isinstance(out["confidence"], float)
