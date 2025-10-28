# tests/test_accuracy_against_csv.py
import csv
import pytest
from app.ai.intent_classification.keyword_matcher import KeywordMatcher

def test_accuracy_csv(tmp_keywords_dir):
    csv_path = os.path.join(os.path.dirname(__file__), "labeled_queries.csv")
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        pytest.skip("labeled_queries.csv not found; skipping accuracy test")

    m = KeywordMatcher(keywords_dir=tmp_keywords_dir)
    total = 0
    correct = 0
    for r in rows:
        q = r.get("query", "")
        expected = r.get("intent", "")
        out = m.match_intent(q)
        total += 1
        if out["action_code"] == expected:
            correct += 1
    accuracy = correct / total if total else 0.0
    assert accuracy >= 0.6, f"Accuracy too low: {accuracy:.3f}"
