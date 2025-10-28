# tests/test_keyword_matcher_unit.py
import time
import pytest

from app.ai.intent_classification.keyword_matcher import KeywordMatcher

def test_preprocess_and_tokenize(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    s = "Checkout!!! Now, please."
    norm = m.preprocess(s)
    assert "checkout" in norm
    assert "now" in norm

def test_exact_phrase_match(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    out = m.match_intent("Please proceed to checkout and finalize my purchase")
    assert "action_code" in out
    assert "confidence" in out
    assert 0.0 <= out["confidence"] <= 1.0

def test_partial_token_match(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    res = m.match_intent("I want to add this to my shopping cart")
    assert isinstance(res["action_code"], str)
    assert isinstance(res["matched_keywords"], list)

def test_punctuation_and_special_chars(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    res = m.match_intent("!! apply coupon @@##")
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0

def test_response_time_small(tmp_keywords_dir):
    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    q = "please add to cart"
    t0 = time.perf_counter()
    out = m.match_intent(q)
    elapsed = (time.perf_counter() - t0) * 1000.0
    assert elapsed < 200.0
