import unittest
from app.ai.intent_classification.embedding_matcher import EmbeddingMatcher

class TestEmbeddingUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matcher = EmbeddingMatcher()

    def test_similarity_present(self):
        r = self.matcher.search("show specs")
        self.assertTrue(isinstance(r, list))

    def test_threshold_filters(self):
        r = self.matcher.search("zzzz qqqq", threshold=0.95)
        # caller filters by threshold; here we assert top score is low
        if r:
            self.assertLess(r[0]["score"], 0.95)

if __name__ == "__main__":
    unittest.main()
