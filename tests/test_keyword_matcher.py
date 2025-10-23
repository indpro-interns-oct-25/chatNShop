# tests/test_keyword_matcher.py
import time
import unittest
from app.ai.intent_classification.keyword_matcher import match_keywords
from app.ai.intent_classification.scoring import calculate_confidence

class TestKeywordMatcher(unittest.TestCase):

    def test_case_insensitive_matching(self):
        text = "Add To CART"
        matches = match_keywords(text)
        self.assertTrue(any(m["intent"] == "ADD_TO_CART" for m in matches))
        self.assertAlmostEqual(calculate_confidence(matches), matches[0]["score"])

    def test_partial_match(self):
        text = "buy this"
        matches = match_keywords(text)
        self.assertTrue(any(m["match_type"] in ("partial", "exact") for m in matches))
        self.assertGreater(calculate_confidence(matches), 0.0)

    def test_multiple_intents(self):
        text = "Can you show specs of iPhone and add to cart?"
        matches = match_keywords(text)
        intents = [m["intent"] for m in matches]
        self.assertIn("PRODUCT_INFO", intents)
        self.assertIn("ADD_TO_CART", intents)

    def test_no_match_scenario(self):
        text = "Blah blah unknown text"
        matches = match_keywords(text)
        self.assertEqual(matches, [])
        self.assertEqual(calculate_confidence(matches), 0.0)

    def test_performance(self):
        text = "Please find the best laptop and add to cart"
        start = time.time()
        matches = match_keywords(text)
        end = time.time()
        elapsed_ms = (end - start) * 1000
        print(f"Performance: {elapsed_ms:.2f}ms")
        self.assertLess(elapsed_ms, 50)

if __name__ == "__main__":
    unittest.main()
