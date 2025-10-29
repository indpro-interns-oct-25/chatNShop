import csv
from app.ai.intent_classification.keyword_matcher import match_keywords

def test_accuracy_against_csv():
    with open("labeled_queries.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        total, correct = 0, 0
        for row in reader:
            total += 1
            result = match_keywords(row["query"], {"greeting": ["hi", "hello"]})
            if result["intent"] == row["label"]:
                correct += 1
        assert (correct / total) >= 0.8
